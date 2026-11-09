import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def desenhar_diagrama():
    fig, ax = plt.subplots(figsize=(20, 12), dpi=250)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 120)
    ax.axis("off")

    # Paleta de Cores BPMN 2.0 Profissional
    c_blue = "#1e40af"       # Azul marinho FIAP/Tech
    c_light_blue = "#dbeafe" # Fundo tarefas
    c_blue_border = "#2563eb"
    c_amber = "#d97706"      # Gateways / Alertas
    c_amber_bg = "#fef3c7"
    c_green = "#16a34a"      # Sucesso / Início
    c_green_bg = "#dcfce7"
    c_red = "#dc2626"        # Rejeição
    c_red_bg = "#fee2e2"
    c_purple = "#7c3aed"     # Pacotes
    c_purple_bg = "#f3e8ff"
    c_sub_bg = "#f8fafc"     # Fundo subprocesso
    c_gray_text = "#334155"

    # Cabeçalho Principal
    ax.text(100, 115, "PASSO SEGURO — FLUXO OPERACIONAL DE TRIAGEM RPA (BPMN 2.0)", 
            fontsize=18, fontweight="bold", ha="center", va="center", color="#0f172a")
    ax.text(100, 111, "Pipeline Automatizada de Higienização, Deduplicação, Enriquecimento GeoSampa e Priorização Infosiga", 
            fontsize=11, ha="center", va="center", color="#64748b")

    # Contêiner do Subprocesso (Isolamento de Falha por Relato - try/except)
    subproc = patches.FancyBboxPatch((24, 18), 136, 88, boxstyle="round,pad=1.2", 
                                    facecolor=c_sub_bg, edgecolor="#94a3b8", linestyle="--", linewidth=1.8)
    ax.add_patch(subproc)
    ax.text(28, 102, "SUBPROCESSO: Triagem Individual por Relato (com Isolamento de Falha try/except)", 
            fontsize=10.5, fontweight="bold", color="#334155")

    # ==========================================
    # 1. INÍCIO DO PROCESSO (Gatilho de Lote)
    # ==========================================
    start_circle = patches.Circle((12, 60), 4.5, facecolor=c_green_bg, edgecolor=c_green, linewidth=2.5)
    ax.add_patch(start_circle)
    ax.text(12, 60, "Início\nLote", fontsize=8.5, fontweight="bold", ha="center", va="center", color=c_green)
    ax.text(12, 52, "Cron (30m) ou\nSob Demanda", fontsize=7, ha="center", color="#64748b")

    # Seta Início -> Tarefa 1 (Coleta API)
    ax.annotate("", xy=(28, 60), xytext=(16.5, 60), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # ==========================================
    # 2. TAREFA 1: Coleta na API Central (Azure)
    # ==========================================
    t1 = patches.FancyBboxPatch((28, 54), 18, 12, boxstyle="round,pad=0.5", 
                               facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.5)
    ax.add_patch(t1)
    ax.text(37, 61, "1. Coletar Novos", fontsize=8, fontweight="bold", ha="center", color=c_blue)
    ax.text(37, 56.5, "GET /api/relatos\n(?status=novo)", fontsize=7, ha="center", color="#1e3a8a")

    # Seta T1 -> Tarefa 2 (Validação de Mídia / Download)
    ax.annotate("", xy=(51, 60), xytext=(46, 60), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # ==========================================
    # 3. TAREFA 2: Download & Validação de Imagem
    # ==========================================
    t2 = patches.FancyBboxPatch((51, 54), 17, 12, boxstyle="round,pad=0.5", 
                               facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.5)
    ax.add_patch(t2)
    ax.text(59.5, 61, "2. Validar Mídia", fontsize=8, fontweight="bold", ha="center", color=c_blue)
    ax.text(59.5, 56.5, "GET /api/fotos/*\nMagic Bytes & Pillow", fontsize=7, ha="center", color="#1e3a8a")

    # Seta T2 -> Gateway 1 (Imagem Válida?)
    ax.annotate("", xy=(72, 60), xytext=(68, 60), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # Gateway 1 (Imagem Válida?)
    gw1 = patches.Polygon([[72, 60], [75.5, 64], [79, 60], [75.5, 56]], facecolor=c_amber_bg, edgecolor=c_amber, linewidth=1.5)
    ax.add_patch(gw1)
    ax.text(75.5, 60, "?", fontsize=9.5, fontweight="bold", ha="center", va="center", color=c_amber)
    ax.text(75.5, 66.5, "GW1: Imagem\nÍntegra?", fontsize=7, fontweight="bold", ha="center", color=c_amber)

    # Desvio GW1 [Não] -> Sobe para Rejeição de Foto
    ax.annotate("", xy=(75.5, 84), xytext=(75.5, 64), arrowprops=dict(arrowstyle="->", color=c_red, lw=1.6))
    ax.text(77.5, 73, "[Não]", fontsize=7.5, fontweight="bold", color=c_red)

    # ==========================================
    # 4. TAREFA 3: Validação Bounding Box SP
    # ==========================================
    # Seta GW1 [Sim] -> T3
    ax.annotate("", xy=(84, 60), xytext=(79, 60), arrowprops=dict(arrowstyle="->", color=c_green, lw=1.8))
    ax.text(81, 62, "[Sim]", fontsize=7, fontweight="bold", color=c_green)

    t3 = patches.FancyBboxPatch((84, 54), 16, 12, boxstyle="round,pad=0.5", 
                               facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.5)
    ax.add_patch(t3)
    ax.text(92, 61, "3. Bounding Box", fontsize=8, fontweight="bold", ha="center", color=c_blue)
    ax.text(92, 56.5, "Limites Geográficos\nMunicípio de SP", fontsize=7, ha="center", color="#1e3a8a")

    # Gateway 2 (Dentro de SP?)
    gw_sp = patches.Polygon([[104, 60], [107.5, 64], [111, 60], [107.5, 56]], facecolor=c_amber_bg, edgecolor=c_amber, linewidth=1.5)
    ax.add_patch(gw_sp)
    ax.text(107.5, 60, "?", fontsize=9.5, fontweight="bold", ha="center", va="center", color=c_amber)
    ax.text(107.5, 66.5, "GW2: Dentro\nde SP?", fontsize=7, fontweight="bold", ha="center", color=c_amber)

    # Seta T3 -> GW_SP
    ax.annotate("", xy=(104, 60), xytext=(100, 60), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # Desvio GW_SP [Não] -> Sobe para Rejeição Territorial
    ax.annotate("", xy=(107.5, 84), xytext=(107.5, 64), arrowprops=dict(arrowstyle="->", color=c_red, lw=1.6))
    ax.text(109.5, 73, "[Não]", fontsize=7.5, fontweight="bold", color=c_red)

    # ==========================================
    # 5. TAREFA 4: Deduplicação Espacial & Temporal
    # ==========================================
    # Seta GW_SP [Sim] -> T4
    ax.annotate("", xy=(116, 60), xytext=(111, 60), arrowprops=dict(arrowstyle="->", color=c_green, lw=1.8))
    ax.text(113, 62, "[Sim]", fontsize=7, fontweight="bold", color=c_green)

    t4 = patches.FancyBboxPatch((116, 54), 17, 12, boxstyle="round,pad=0.5", 
                               facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.5)
    ax.add_patch(t4)
    ax.text(124.5, 61, "4. Deduplicação", fontsize=8, fontweight="bold", ha="center", color=c_blue)
    ax.text(124.5, 56.5, "Haversine < 30m &\nJanela < 14 dias", fontsize=7, ha="center", color="#1e3a8a")

    # Gateway 3 (Duplicado?)
    gw_dup = patches.Polygon([[137, 60], [140.5, 64], [144, 60], [140.5, 56]], facecolor=c_amber_bg, edgecolor=c_amber, linewidth=1.5)
    ax.add_patch(gw_dup)
    ax.text(140.5, 60, "?", fontsize=9.5, fontweight="bold", ha="center", va="center", color=c_amber)
    ax.text(140.5, 66.5, "GW3: É\nDuplicado?", fontsize=7, fontweight="bold", ha="center", color=c_amber)

    # Seta T4 -> GW_DUP
    ax.annotate("", xy=(137, 60), xytext=(133, 60), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # Desvio GW_DUP [Sim, Duplicado] -> Sobe para Rejeição por Duplicidade
    ax.annotate("", xy=(140.5, 84), xytext=(140.5, 64), arrowprops=dict(arrowstyle="->", color=c_red, lw=1.6))
    ax.text(142.5, 73, "[Sim]", fontsize=7.5, fontweight="bold", color=c_red)

    # =========================================================================
    # RAMO SUPERIOR: FLUXO DE REJEIÇÃO / DESCARTE (COM EVENTO FIM ESPECÍFICO)
    # =========================================================================
    t_rej = patches.FancyBboxPatch((68, 84), 80, 11, boxstyle="round,pad=0.5", 
                                  facecolor=c_red_bg, edgecolor=c_red, linewidth=1.6)
    ax.add_patch(t_rej)
    ax.text(108, 91.5, "Atualizar Status na API: PATCH /api/relatos/{id} -> status='rejeitado'", 
            fontsize=7.5, fontweight="bold", ha="center", color="#991b1b")
    ax.text(108, 86.5, "Registra motivo técnico da recusa (imagem inválida / fora de SP / duplicidade) e audita em log", 
            fontsize=6.8, ha="center", color="#7f1d1d")

    # Seta Rejeição -> EVENTO FIM: DESCARTE
    ax.annotate("", xy=(153, 89.5), xytext=(148, 89.5), arrowprops=dict(arrowstyle="->", color=c_red, lw=2))

    # EVENTO FIM 1: DESCARTE (Círculo Duplo Vermelho)
    end_rej_outer = patches.Circle((156, 89.5), 3.2, facecolor=c_red_bg, edgecolor=c_red, linewidth=2.5)
    end_rej_inner = patches.Circle((156, 89.5), 2.2, facecolor=c_red_bg, edgecolor=c_red, linewidth=1.5)
    ax.add_patch(end_rej_outer)
    ax.add_patch(end_rej_inner)
    ax.text(156, 83.5, "FIM:\nDescarte", fontsize=7, fontweight="bold", ha="center", color=c_red)

    # =========================================================================
    # RAMO INFERIOR: PROCESSAMENTO VÁLIDO (ENRIQUECIMENTO E PRIORIDADE)
    # =========================================================================
    # Seta GW_DUP [Não, Inédito] -> Desce para Linha Inferior
    ax.annotate("", xy=(140.5, 47), xytext=(140.5, 56), arrowprops=dict(arrowstyle="->", color=c_green, lw=1.8))
    ax.text(142.5, 51.5, "[Não]", fontsize=7, fontweight="bold", color=c_green)

    # Tarefa 5: Enriquecimento Territorial GeoSampa
    t5 = patches.FancyBboxPatch((124, 35), 23, 12, boxstyle="round,pad=0.5", 
                               facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.5)
    ax.add_patch(t5)
    ax.text(135.5, 42, "5. GeoSampa Territorial", fontsize=8, fontweight="bold", ha="center", color=c_blue)
    ax.text(135.5, 37.5, "Point-in-Polygon\n(32 Subprefeituras)", fontsize=7, ha="center", color="#1e3a8a")

    # Seta T5 -> Visão / Gateway IA
    ax.annotate("", xy=(118, 41), xytext=(124, 41), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # Tarefa: Inferência de Visão Computacional (YOLOv8)
    t_vis = patches.FancyBboxPatch((98, 35), 20, 12, boxstyle="round,pad=0.5", 
                                  facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.5)
    ax.add_patch(t_vis)
    ax.text(108, 42, "Microsserviço Visão", fontsize=8, fontweight="bold", ha="center", color=c_blue)
    ax.text(108, 37.5, "POST /predict (YOLOv8)\nClasses & Severidade", fontsize=7, ha="center", color="#1e3a8a")

    # Seta Visão -> Gateway 4 (Confiança Visão)
    ax.annotate("", xy=(92, 41), xytext=(98, 41), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # Gateway 4 (Confiança da Visão >= 0.60?)
    gw_vis = patches.Polygon([[86, 41], [89, 45], [92, 41], [89, 37]], facecolor=c_amber_bg, edgecolor=c_amber, linewidth=1.5)
    ax.add_patch(gw_vis)
    ax.text(89, 41, "?", fontsize=9, fontweight="bold", ha="center", va="center", color=c_amber)
    ax.text(89, 47.5, "GW4: Confiança\n>= 0.60?", fontsize=7, fontweight="bold", ha="center", color=c_amber)

    # -------------------------------------------------------------------------
    # DESVIO: REVISÃO HUMANA (COM EVENTO FIM ESPECÍFICO)
    # -------------------------------------------------------------------------
    ax.annotate("", xy=(89, 28), xytext=(89, 37), arrowprops=dict(arrowstyle="->", color=c_amber, lw=1.8))
    ax.text(91, 32, "[<0.60]", fontsize=7, fontweight="bold", color=c_amber)

    t_rev = patches.FancyBboxPatch((76, 21), 26, 7, boxstyle="round,pad=0.5", 
                                  facecolor="#fef9c3", edgecolor="#ca8a04", linewidth=1.5)
    ax.add_patch(t_rev)
    ax.text(89, 24.5, "PATCH /relatos/{id} -> 'revisao_humana'", fontsize=6.8, fontweight="bold", ha="center", va="center", color="#854d0e")

    # Seta Revisão Humana -> EVENTO FIM: FILA HUMANA
    ax.annotate("", xy=(69, 24.5), xytext=(76, 24.5), arrowprops=dict(arrowstyle="->", color="#ca8a04", lw=2))

    # EVENTO FIM 2: REVISÃO HUMANA (Círculo Duplo Âmbar)
    end_rev_outer = patches.Circle((65, 24.5), 3.2, facecolor="#fef9c3", edgecolor="#ca8a04", linewidth=2.5)
    end_rev_inner = patches.Circle((65, 24.5), 2.2, facecolor="#fef9c3", edgecolor="#ca8a04", linewidth=1.5)
    ax.add_patch(end_rev_outer)
    ax.add_patch(end_rev_inner)
    ax.text(65, 29.5, "FIM:\nFila Humana", fontsize=7, fontweight="bold", ha="center", color="#854d0e")

    # -------------------------------------------------------------------------
    # FLUXO PRINCIPAL: PRIORIZAÇÃO INFOSIGA & DESPACHO
    # -------------------------------------------------------------------------
    # Seta GW4 [>=0.60] -> Tarefa Cálculo de Prioridade
    ax.annotate("", xy=(80, 41), xytext=(86, 41), arrowprops=dict(arrowstyle="->", color=c_green, lw=1.8))
    ax.text(83, 42.5, "[Sim]", fontsize=7, fontweight="bold", color=c_green)

    t_prio = patches.FancyBboxPatch((55, 35), 25, 12, boxstyle="round,pad=0.5", 
                                   facecolor=c_green_bg, edgecolor=c_green, linewidth=1.5)
    ax.add_patch(t_prio)
    ax.text(67.5, 42, "6. Matriz de Prioridade", fontsize=8, fontweight="bold", ha="center", color="#14532d")
    ax.text(67.5, 37.5, "Cruzamento Infosiga (Sinistros)\nScore: ALTA / NORMAL / BAIXA", fontsize=6.8, ha="center", color="#15803d")

    # Seta Prioridade -> PATCH /relatos/{id} "encaminhado"
    ax.annotate("", xy=(49, 41), xytext=(55, 41), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    t_patch = patches.FancyBboxPatch((28, 35), 21, 12, boxstyle="round,pad=0.5", 
                                    facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.5)
    ax.add_patch(t_patch)
    ax.text(38.5, 42, "7. Atualizar API", fontsize=8, fontweight="bold", ha="center", color=c_blue)
    ax.text(38.5, 37.5, "PATCH /api/relatos/{id}\n'encaminhado' + subpref", fontsize=6.8, ha="center", color="#1e3a8a")

    # EVENTO FIM 3: APROVADO PARA LOTE (Círculo Duplo Verde)
    ax.annotate("", xy=(38.5, 28), xytext=(38.5, 35), arrowprops=dict(arrowstyle="->", color=c_green, lw=2))
    end_app_outer = patches.Circle((38.5, 24.5), 3.2, facecolor=c_green_bg, edgecolor=c_green, linewidth=2.5)
    end_app_inner = patches.Circle((38.5, 24.5), 2.2, facecolor=c_green_bg, edgecolor=c_green, linewidth=1.5)
    ax.add_patch(end_app_outer)
    ax.add_patch(end_app_inner)
    ax.text(38.5, 29.5, "FIM: Aprovado\n(Vai p/ Lote)", fontsize=7, fontweight="bold", ha="center", color=c_green)

    # =========================================================================
    # CONSOLIDAÇÃO DO LOTE (FORA DO SUBPROCESSO)
    # =========================================================================
    # Seta Subprocesso -> Compilação de Pacotes
    ax.annotate("", xy=(165, 62), xytext=(160, 62), arrowprops=dict(arrowstyle="->", color="#334155", lw=2.2))

    t_pacote = patches.FancyBboxPatch((165, 52), 30, 20, boxstyle="round,pad=0.8", 
                                     facecolor=c_purple_bg, edgecolor=c_purple, linewidth=2)
    ax.add_patch(t_pacote)
    ax.text(180, 65, "8. Pacotes SP156", fontsize=9.5, fontweight="bold", ha="center", color=c_purple)
    ax.text(180, 58, "Agrupamento por Subprefeitura:\n• CSV Oficial Formatado\n• Relatório PDF Oficial\n(dist/pacotes/)", 
            fontsize=7.5, ha="center", color="#581c87")

    # Tarefa 9: Auditoria LGPD e Logs
    t_resumo = patches.FancyBboxPatch((165, 24), 30, 20, boxstyle="round,pad=0.8", 
                                     facecolor="#f1f5f9", edgecolor="#64748b", linewidth=1.8)
    ax.add_patch(t_resumo)
    ax.text(180, 36.5, "9. Auditoria & LGPD", fontsize=9, fontweight="bold", ha="center", color="#334155")
    ax.text(180, 30, "• Logs Estruturados JSONL\n• Anonimização e Hash LGPD\n• Resumo Executivo no Terminal", 
            fontsize=7.5, ha="center", color="#475569")
    ax.annotate("", xy=(180, 44), xytext=(180, 52), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # =========================================================================
    # EVENTO FINAL GERAL: FIM DO LOTE
    # =========================================================================
    ax.annotate("", xy=(180, 15.5), xytext=(180, 24), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=2.2))

    end_lote_outer = patches.Circle((180, 11), 4.2, facecolor="#e2e8f0", edgecolor="#0f172a", linewidth=3)
    end_lote_inner = patches.Circle((180, 11), 3.0, facecolor="#0f172a", edgecolor="#0f172a", linewidth=1)
    ax.add_patch(end_lote_outer)
    ax.add_patch(end_lote_inner)
    ax.text(180, 11, "FIM", fontsize=7.5, fontweight="bold", ha="center", va="center", color="#ffffff")
    ax.text(180, 4.5, "Fim da Execução\ndo Lote RPA", fontsize=7.5, fontweight="bold", ha="center", color="#0f172a")

    # Rodapé com Metadados Oficiais FIAP
    ax.text(10, 3, "Passo Seguro RPA v1.0.0 | FIAP CitizenTech — São Paulo 2026", 
            fontsize=8.5, color="#64748b")
    ax.text(195, 3, "Padrão BPMN 2.0 Estrito | Todos os ramos encerram em Nós Finais (End Events)", 
            fontsize=8.5, ha="right", color="#64748b")

    plt.tight_layout()
    
    docs_png = Path("docs/triagem_processo.png")
    assets_png = Path("assets/triagem_processo.png")
    assets_png.parent.mkdir(parents=True, exist_ok=True)
    docs_png.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(docs_png, dpi=250, bbox_inches="tight")
    plt.savefig(assets_png, dpi=250, bbox_inches="tight")
    plt.close(fig)
    print(f"Diagrama BPMN 2.0 atualizado e salvo com sucesso em {docs_png} e {assets_png}")


if __name__ == "__main__":
    desenhar_diagrama()
