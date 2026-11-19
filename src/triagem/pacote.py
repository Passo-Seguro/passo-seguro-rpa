import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from fpdf import FPDF

from src.triagem.config import settings
from src.triagem.validacao import mascarar_lgpd


def limpar_texto_pdf(texto: str) -> str:
    """Substitui caracteres fora do padrão latin-1 (como travessões) para compatibilidade com fpdf."""
    if not texto:
        return ""
    texto = texto.replace("—", "-").replace("–", "-").replace("“", '"').replace("”", '"').replace("’", "'")
    return texto.encode("latin-1", "replace").decode("latin-1")


class RelatorioPDF(FPDF):
    """Template PDF customizado para exportação oficial de despachos da zeladoria urbana."""

    def __init__(self, subprefeitura: str, data_str: str, hora_atualizacao: str = ""):
        super().__init__()
        self.subprefeitura = limpar_texto_pdf(subprefeitura)
        self.data_str = data_str
        self.hora_atualizacao = hora_atualizacao or datetime.now(timezone.utc).strftime("%H:%M:%S")

    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 7, "Passo Seguro - CitizenTech SP | Zeladoria Urbana", new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_font("Helvetica", "", 9.5)
        self.cell(0, 5, f"Pacote de Despacho Operacional SP156 | Subprefeitura: {self.subprefeitura} | Data: {self.data_str} (Atualizado: {self.hora_atualizacao})", new_x="LMARGIN", new_y="NEXT", align="L")
        self.line(10, 24, 200, 24)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()} | Consolidacao Diaria Passo Seguro RPA (LGPD Compliant)", align="C")


def gerar_pacotes_despacho(relatos_processados: List[Dict[str, Any]], data_lote: str = None) -> Dict[str, Dict[str, Path]]:
    """
    Agrupa os relatos encaminhados/validados por Subprefeitura e gera os arquivos CSV e PDF
    em dist/pacotes/{data}/.
    Mantém UM relatório PDF e UM CSV por dia por subprefeitura, atualizados a cada execução
    com todos os chamados triados desde o primeiro até o último processamento do dia.
    """
    agora_utc = datetime.now(timezone.utc)
    if not data_lote:
        data_lote = agora_utc.strftime("%Y-%m-%d")
    hora_atual_str = agora_utc.strftime("%H:%M:%S")

    diretorio_destino = settings.dist_dir / data_lote
    diretorio_destino.mkdir(parents=True, exist_ok=True)

    # Filtra apenas itens que devem ser despachados para a zeladoria municipal
    relatos_validos = [
        r for r in relatos_processados
        if r.get("status") in ["validado", "encaminhado"]
    ]

    # Agrupamento por subprefeitura
    por_subprefeitura: Dict[str, List[Dict[str, Any]]] = {}
    for r in relatos_validos:
        sub = r.get("subprefeitura") or "Outras_Regioes"
        por_subprefeitura.setdefault(sub, []).append(r)

    arquivos_gerados: Dict[str, Dict[str, Path]] = {}

    for sub, novos_itens in por_subprefeitura.items():
        sub_slug = sub.lower().replace(" ", "_").replace("/", "-")
        caminho_csv = diretorio_destino / f"pacote_SP156_{sub_slug}_{data_lote}.csv"
        caminho_pdf = diretorio_destino / f"relatorio_SP156_{sub_slug}_{data_lote}.pdf"

        # Consolidação Diária (Append Inteligente e Histórico Completo do Dia):
        itens_consolidados: List[Dict[str, Any]] = []
        ids_vistos = set()

        if caminho_csv.exists():
            try:
                with open(caminho_csv, mode="r", encoding="utf-8") as f_existente:
                    reader = csv.DictReader(f_existente)
                    for row in reader:
                        relato_id = row.get("id_relato")
                        if relato_id and relato_id not in ids_vistos:
                            ids_vistos.add(relato_id)
                            itens_consolidados.append({
                                "id": relato_id,
                                "timestamp": row.get("data_hora_registro") or row.get("data_hora"),
                                "triado_em": row.get("horario_triagem_rpa") or "N/D",
                                "subprefeitura": row.get("subprefeitura"),
                                "distrito": row.get("distrito"),
                                "tipo": row.get("tipo_avaria"),
                                "prioridade": row.get("prioridade", "NORMAL"),
                                "latitude": row.get("latitude"),
                                "longitude": row.get("longitude"),
                                "descricao": row.get("descricao_sanitizada", ""),
                                "motivo_decisao": row.get("justificativa_prioridade", "")
                            })
            except Exception:
                pass

        for item in novos_itens:
            relato_id = item.get("id")
            if relato_id not in ids_vistos:
                ids_vistos.add(relato_id)
                # Garante timestamps de criação e de triagem pelo RPA
                if "triado_em" not in item:
                    item["triado_em"] = f"{data_lote} {hora_atual_str}"
                itens_consolidados.append(item)

        # 1. Exportação CSV Consolidado do Dia com Timestamps
        with open(caminho_csv, mode="w", newline="", encoding="utf-8") as f_csv:
            writer = csv.writer(f_csv)
            writer.writerow([
                "id_relato", "data_hora_registro", "horario_triagem_rpa", "subprefeitura", "distrito", "tipo_avaria",
                "prioridade", "latitude", "longitude", "descricao_sanitizada", "justificativa_prioridade"
            ])
            for item in itens_consolidados:
                writer.writerow([
                    item.get("id"),
                    item.get("timestamp") or "N/D",
                    item.get("triado_em") or f"{data_lote} {hora_atual_str}",
                    item.get("subprefeitura"),
                    item.get("distrito"),
                    item.get("tipo"),
                    item.get("prioridade", "NORMAL"),
                    item.get("latitude"),
                    item.get("longitude"),
                    mascarar_lgpd(item.get("descricao", "")),
                    item.get("motivo_decisao", "")
                ])

        # 2. Exportação PDF Consolidado (Recriado com todos os itens do dia, métricas e timestamps)
        pdf = RelatorioPDF(subprefeitura=sub, data_str=data_lote, hora_atualizacao=hora_atual_str)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Resumo Estatístico do Pacote Consolidado Diário
        total_itens = len(itens_consolidados)
        qtd_alta = sum(1 for i in itens_consolidados if i.get("prioridade") == "ALTA")
        qtd_normal = sum(1 for i in itens_consolidados if i.get("prioridade") == "NORMAL")
        qtd_baixa = sum(1 for i in itens_consolidados if i.get("prioridade") == "BAIXA")

        pdf.set_font("Helvetica", "B", 9.5)
        resumo_header = limpar_texto_pdf(f"Relatorio Consolidado do Dia: {total_itens} chamados despachados (Prioridade ALTA: {qtd_alta} | NORMAL: {qtd_normal} | BAIXA: {qtd_baixa})")
        pdf.set_x(10)
        pdf.cell(pdf.epw, 5.5, resumo_header, new_x="LMARGIN", new_y="NEXT")

        horarios = [str(i.get("triado_em")) for i in itens_consolidados if i.get("triado_em") and i.get("triado_em") != "N/D"]
        if horarios:
            primeiro_lote = min(horarios)
            ultimo_lote = max(horarios)
            pdf.set_font("Helvetica", "I", 8)
            pdf.cell(pdf.epw, 4, limpar_texto_pdf(f"Intervalo operacional: primeiro chamado triado as {primeiro_lote} | ultimo as {ultimo_lote}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Listagem de Ocorrências com Timestamps
        for idx, item in enumerate(itens_consolidados, start=1):
            pdf.set_font("Helvetica", "B", 9)
            cor_prioridade = (200, 30, 30) if item.get("prioridade") == "ALTA" else (30, 100, 30)
            pdf.set_text_color(*cor_prioridade)
            titulo_item = limpar_texto_pdf(f"#{idx} [{item.get('prioridade')}] {item.get('tipo', '').upper()} - ID: {item.get('id')}")
            pdf.cell(0, 5, titulo_item, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)

            # Timestamps
            pdf.set_font("Helvetica", "", 7.5)
            h_reg = item.get("timestamp") or "N/D"
            h_tri = item.get("triado_em") or f"{data_lote} {hora_atual_str}"
            linha_tempo = limpar_texto_pdf(f"Registro Cidadao: {h_reg} | Captura e Triagem RPA: {h_tri}")
            pdf.set_x(10)
            pdf.cell(pdf.epw, 3.8, linha_tempo, new_x="LMARGIN", new_y="NEXT")

            # Localização
            pdf.set_font("Helvetica", "", 8)
            coord_str = limpar_texto_pdf(f"Coordenadas: Lat {item.get('latitude')}, Lon {item.get('longitude')} | Distrito: {item.get('distrito', 'N/D')}")
            pdf.set_x(10)
            pdf.cell(pdf.epw, 4, coord_str, new_x="LMARGIN", new_y="NEXT")

            desc = limpar_texto_pdf(f"Descricao: {mascarar_lgpd(item.get('descricao', ''))}")
            pdf.set_x(10)
            pdf.multi_cell(w=pdf.epw, h=4, text=desc)

            just = item.get("motivo_decisao", "")
            if just:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_x(10)
                pdf.multi_cell(w=pdf.epw, h=4, text=limpar_texto_pdf(f"Criterio da Esteira: {just}"))

            pdf.ln(2.5)

        pdf.output(str(caminho_pdf))

        arquivos_gerados[sub] = {
            "csv": caminho_csv,
            "pdf": caminho_pdf,
            "total_itens": len(itens_consolidados)
        }

    return arquivos_gerados
