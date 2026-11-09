import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from src.triagem.config import settings
from src.triagem.cliente_api import ClienteAPI
from src.triagem.validacao import validar_imagem, validar_coordenadas_sp, sanitizar_relato_lgpd
from src.triagem.deduplicacao import verificar_duplicidade
from src.triagem.geo import identificar_territorio
from src.triagem.prioridade import avaliar_prioridade_e_status
from src.triagem.pacote import gerar_pacotes_despacho


class JSONLinesLogger:
    """Logger estruturado em formato JSON Lines, em total conformidade com a LGPD."""

    def __init__(self, log_dir: Path = Path("logs")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"triagem_{hoje}.log"
        self.sample_file = self.log_dir / "execucao_amostra.jsonl"

    def log_evento(self, item_id: str, etapa: str, status: str, mensagem: str):
        item_hash = hashlib.sha256(item_id.encode("utf-8")).hexdigest()[:12] if item_id else "global"
        evento = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "item_hash": item_hash,
            "etapa": etapa,
            "status": status,
            "mensagem": mensagem
        }
        linha = json.dumps(evento, ensure_ascii=False)

        # Imprime no terminal de forma legível
        cor = "\033[92m" if status == "sucesso" else ("\033[93m" if status == "alerta" else "\033[91m")
        reset = "\033[0m"
        print(f"[{evento['timestamp']}] {cor}[{status.upper()}]{reset} ({etapa}) #{item_hash}: {mensagem}")

        # Grava nos arquivos de log
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(linha + "\n")

        with open(self.sample_file, "a", encoding="utf-8") as f:
            f.write(linha + "\n")


def processar_lote_triagem(
    cliente: ClienteAPI,
    logger: JSONLinesLogger,
    historico_acumulado: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Executa a esteira de triagem sobre todos os relatos pendentes.
    Possui isolamento total de falha por relato (try/except individual).
    """
    inicio_lote = datetime.now(timezone.utc)
    relatos = cliente.buscar_relatos_novos()

    metricas = {
        "processados": 0,
        "encaminhados": 0,
        "revisao_humana": 0,
        "duplicados": 0,
        "rejeitados": 0,
        "erros": 0
    }

    relatos_processados_neste_lote = []

    print("\n" + "=" * 70)
    print(f" INICIANDO PROCESSAMENTO DE LOTE: {len(relatos)} RELATOS DETECTADOS")
    print("=" * 70)

    for relato in relatos:
        id_relato = relato.get("id", "sem-id")
        metricas["processados"] += 1

        try:
            # 1. Validação de Imagem
            foto_origem = relato.get("foto_url") or relato.get("imagem_base64") or ""
            valida_img, motivo_img = validar_imagem(foto_origem)
            if not valida_img:
                logger.log_evento(id_relato, "validacao_imagem", "erro", f"Imagem rejeitada: {motivo_img}")
                cliente.atualizar_status_relato(id_relato, "rejeitado", motivo=f"imagem_invalida: {motivo_img}")
                relato["status"] = "rejeitado"
                relato["motivo_decisao"] = motivo_img
                metricas["rejeitados"] += 1
                continue

            logger.log_evento(id_relato, "validacao_imagem", "sucesso", "Buffer de mídia verificado e íntegro")

            # 2. Validação Territorial Prévia (Bounding Box SP)
            lat = relato.get("latitude")
            lon = relato.get("longitude")
            if lat is None or lon is None:
                logger.log_evento(id_relato, "validacao_geo", "erro", "Coordenadas geográficas ausentes")
                cliente.atualizar_status_relato(id_relato, "rejeitado", motivo="coordenadas_ausentes")
                relato["status"] = "rejeitado"
                metricas["rejeitados"] += 1
                continue

            valida_bb, motivo_bb = validar_coordenadas_sp(lat, lon)
            if not valida_bb:
                logger.log_evento(id_relato, "validacao_geo", "erro", f"Descarte territorial: {motivo_bb}")
                cliente.atualizar_status_relato(id_relato, "rejeitado", motivo="fora_municipio_sp")
                relato["status"] = "rejeitado"
                relato["motivo_decisao"] = motivo_bb
                metricas["rejeitados"] += 1
                continue

            logger.log_evento(id_relato, "validacao_geo", "sucesso", "Coordenadas validadas nos limites de SP")

            # 3. Deduplicação Espacial (30m) e Temporal (14 dias)
            is_dup, motivo_dup = verificar_duplicidade(relato, historico_acumulado)
            if is_dup:
                logger.log_evento(id_relato, "deduplicacao", "alerta", f"Descarte por duplicidade: {motivo_dup}")
                cliente.atualizar_status_relato(id_relato, "rejeitado", motivo=f"duplicidade_geografica: {motivo_dup}")
                relato["status"] = "rejeitado"
                relato["motivo_decisao"] = motivo_dup
                metricas["duplicados"] += 1
                metricas["rejeitados"] += 1
                continue

            logger.log_evento(id_relato, "deduplicacao", "sucesso", "Ocorrência inédita no raio geográfico")

            # 4. Enriquecimento Territorial (Point-in-Polygon GeoSampa)
            territorio = identificar_territorio(lat, lon)
            if not territorio:
                logger.log_evento(id_relato, "geo_enrichment", "alerta", "Ponto fora dos polígonos mapeados de subprefeituras")
                subprefeitura = "Outras_Regioes"
                distrito = "Não Identificado"
            else:
                subprefeitura = territorio["subprefeitura"]
                distrito = territorio["distrito"]
                logger.log_evento(id_relato, "geo_enrichment", "sucesso", f"Território: Subprefeitura {subprefeitura} / Distrito {distrito}")

            relato["subprefeitura"] = subprefeitura
            relato["distrito"] = distrito

            # 5. Gateway de Decisão & Matriz de Prioridade
            dados_visao = relato.get("visao")
            if dados_visao is None and not cliente.mock_mode and foto_origem:
                dados_visao = cliente.solicitar_deteccao_visao(foto_origem)
                if dados_visao is None:
                    logger.log_evento(id_relato, "deteccao_visao", "alerta", "Serviço de visão indisponível após 3 tentativas; degradando suavemente.")
                else:
                    relato["visao"] = dados_visao

            status_decidido, prioridade, justificativa = avaliar_prioridade_e_status(relato, dados_visao)

            relato["prioridade"] = prioridade
            relato["motivo_decisao"] = justificativa

            if status_decidido == "revisao_humana":
                logger.log_evento(id_relato, "decisao_prioridade", "alerta", f"Encaminhado para triagem humana: {justificativa}")
                cliente.atualizar_status_relato(
                    id_relato,
                    "revisao_humana",
                    motivo=justificativa,
                    prioridade=prioridade,
                    subprefeitura=subprefeitura
                )
                relato["status"] = "revisao_humana"
                metricas["revisao_humana"] += 1
            else:
                # Ocorrência validada e apta a despacho
                logger.log_evento(id_relato, "decisao_prioridade", "sucesso", f"Classificado com Prioridade {prioridade}: {justificativa}")
                cliente.atualizar_status_relato(
                    id_relato,
                    "encaminhado",
                    motivo=justificativa,
                    prioridade=prioridade,
                    subprefeitura=subprefeitura,
                    dados_complementares={"prioridade": prioridade, "subprefeitura": subprefeitura}
                )
                relato["status"] = "encaminhado"
                metricas["encaminhados"] += 1

            historico_acumulado.append(relato)
            relatos_processados_neste_lote.append(sanitizar_relato_lgpd(relato))

        except Exception as e:
            logger.log_evento(id_relato, "processamento", "erro", f"Exceção não tratada no item: {str(e)}")
            metricas["erros"] += 1

    # 6. Compilação e Geração de Pacotes de Despacho (CSV e PDF)
    pacotes = gerar_pacotes_despacho(relatos_processados_neste_lote)

    # 7. Exibição do Resumo Consolidado
    duracao = (datetime.now(timezone.utc) - inicio_lote).total_seconds()
    print("\n" + "=" * 70)
    print(" RESUMO DA EXECUÇÃO DO LOTE (PASSO SEGURO RPA)")
    print("=" * 70)
    print(f" • Duração da Esteira:       {duracao:.2f}s")
    print(f" • Total de Relatos:         {metricas['processados']}")
    print(f" • Encaminhados p/ Despacho: \033[92m{metricas['encaminhados']}\033[0m")
    print(f" • Revisão Humana:           \033[93m{metricas['revisao_humana']}\033[0m")
    print(f" • Descartados Duplicados:   \033[93m{metricas['duplicados']}\033[0m")
    print(f" • Rejeitados (Inválidos):   \033[91m{metricas['rejeitados']}\033[0m")
    print(f" • Falhas / Erros:           {metricas['erros']}")
    print("-" * 70)
    print(f" Pacotes SP156 Gerados por Subprefeitura ({len(pacotes)} regiões):")
    for sub, arqs in pacotes.items():
        print(f"   [{sub}] -> {arqs['total_itens']} itens")
        print(f"       CSV: {arqs['csv']}")
        print(f"       PDF: {arqs['pdf']}")
    print("=" * 70 + "\n")

    return {
        "metricas": metricas,
        "pacotes": pacotes
    }


def main():
    parser = argparse.ArgumentParser(description="Passo Seguro — Esteira RPA de Triagem Operacional")
    parser.add_argument("--executar-uma-vez", action="store_true", help="Executa um único ciclo de lote e encerra")
    parser.add_argument("--token", type=str, default=None, help="Token Bearer de autenticação da API (SERVICE_TOKEN)")
    parser.add_argument("--mock-data", type=str, default=None, help="Caminho para arquivo JSON de mock para testes locais")
    parser.add_argument("--intervalo", type=int, default=settings.intervalo_execucao_minutos, help="Intervalo em minutos entre execuções contínuas")

    args = parser.parse_args()

    token = args.token or settings.service_token
    cliente = ClienteAPI(service_token=token)
    logger = JSONLinesLogger()
    historico_acumulado = []

    if args.mock_data:
        caminho_mock = Path(args.mock_data)
        if not caminho_mock.exists():
            print(f"Arquivo mock não encontrado: {caminho_mock}")
            sys.exit(1)
        with open(caminho_mock, "r", encoding="utf-8") as f:
            dados_mock = json.load(f)
        cliente.set_mock_data(dados_mock)
        print(f"Carregados {len(dados_mock)} relatos simulados a partir de {caminho_mock}")

    if args.executar_uma_vez:
        processar_lote_triagem(cliente, logger, historico_acumulado)
    else:
        print(f"Iniciando serviço de triagem contínua (agendamento a cada {args.intervalo} minutos)...")
        try:
            while True:
                processar_lote_triagem(cliente, logger, historico_acumulado)
                time.sleep(args.intervalo * 60)
        except KeyboardInterrupt:
            print("\nServiço interrompido pelo operador.")


if __name__ == "__main__":
    main()
