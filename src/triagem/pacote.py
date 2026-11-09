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

    def __init__(self, subprefeitura: str, data_str: str):
        super().__init__()
        self.subprefeitura = limpar_texto_pdf(subprefeitura)
        self.data_str = data_str

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, "Passo Seguro - CitizenTech SP", new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, f"Pacote de Despacho Operacional SP156 | Subprefeitura: {self.subprefeitura} | Data: {self.data_str}", new_x="LMARGIN", new_y="NEXT", align="L")
        self.line(10, 26, 200, 26)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()} | Gerado por Passo Seguro RPA (LGPD Compliant)", align="C")


def gerar_pacotes_despacho(relatos_processados: List[Dict[str, Any]], data_lote: str = None) -> Dict[str, Dict[str, Path]]:
    """
    Agrupa os relatos encaminhados/validados por Subprefeitura e gera os arquivos CSV e PDF
    em dist/pacotes/{data}/.
    """
    if not data_lote:
        data_lote = datetime.now(timezone.utc).strftime("%Y-%m-%d")

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

    for sub, itens in por_subprefeitura.items():
        sub_slug = sub.lower().replace(" ", "_").replace("/", "-")
        caminho_csv = diretorio_destino / f"pacote_SP156_{sub_slug}_{data_lote}.csv"
        caminho_pdf = diretorio_destino / f"relatorio_SP156_{sub_slug}_{data_lote}.pdf"

        # 1. Exportação CSV
        with open(caminho_csv, mode="w", newline="", encoding="utf-8") as f_csv:
            writer = csv.writer(f_csv)
            writer.writerow([
                "id_relato", "data_hora", "subprefeitura", "distrito", "tipo_avaria",
                "prioridade", "latitude", "longitude", "descricao_sanitizada", "justificativa_prioridade"
            ])
            for item in itens:
                writer.writerow([
                    item.get("id"),
                    item.get("timestamp"),
                    item.get("subprefeitura"),
                    item.get("distrito"),
                    item.get("tipo"),
                    item.get("prioridade", "NORMAL"),
                    item.get("latitude"),
                    item.get("longitude"),
                    mascarar_lgpd(item.get("descricao", "")),
                    item.get("motivo_decisao", "")
                ])

        # 2. Exportação PDF
        pdf = RelatorioPDF(subprefeitura=sub, data_str=data_lote)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Resumo Estatístico do Pacote
        total_itens = len(itens)
        qtd_alta = sum(1 for i in itens if i.get("prioridade") == "ALTA")
        qtd_normal = sum(1 for i in itens if i.get("prioridade") == "NORMAL")
        qtd_baixa = sum(1 for i in itens if i.get("prioridade") == "BAIXA")

        pdf.set_font("Helvetica", "B", 10)
        resumo_header = limpar_texto_pdf(f"Total de Chamados Triados: {total_itens} (Prioridade ALTA: {qtd_alta} | NORMAL: {qtd_normal} | BAIXA: {qtd_baixa})")
        pdf.set_x(10)
        pdf.cell(pdf.epw, 6, resumo_header, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Listagem de Ocorrências
        for idx, item in enumerate(itens, start=1):
            pdf.set_font("Helvetica", "B", 9)
            cor_prioridade = (200, 30, 30) if item.get("prioridade") == "ALTA" else (30, 100, 30)
            pdf.set_text_color(*cor_prioridade)
            titulo_item = limpar_texto_pdf(f"#{idx} [{item.get('prioridade')}] {item.get('tipo', '').upper()} - ID: {item.get('id')}")
            pdf.cell(0, 5, titulo_item, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)

            pdf.set_font("Helvetica", "", 8)
            coord_str = limpar_texto_pdf(f"Lat: {item.get('latitude')}, Lon: {item.get('longitude')} | Distrito: {item.get('distrito', 'N/D')}")
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

            pdf.ln(2)

        pdf.output(str(caminho_pdf))

        arquivos_gerados[sub] = {
            "csv": caminho_csv,
            "pdf": caminho_pdf,
            "total_itens": len(itens)
        }

    return arquivos_gerados
