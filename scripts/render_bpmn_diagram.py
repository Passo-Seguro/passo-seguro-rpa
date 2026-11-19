import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def desenhar_diagrama():
    # Canvas horizontal panorâmico compacto (proporção 16:7 ideal para slides, docs e visualização sem rolagem)
    fig, ax = plt.subplots(figsize=(21, 7.5), dpi=260)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    ax.set_xlim(3, 235)
    ax.set_ylim(14, 86)
    ax.axis("off")

    # Paleta de Cores BPMN 2.0
    c_blue = "#1e40af"        # Azul escuro títulos
    c_light_blue = "#eff6ff"  # Fundo tarefas
    c_blue_border = "#3b82f6" # Borda tarefas
    c_amber = "#b45309"       # Gateways e Alertas
    c_amber_bg = "#fef3c7"
    c_amber_border = "#f59e0b"
    c_green = "#15803d"       # Sucesso / Início
    c_green_bg = "#dcfce7"
    c_green_border = "#22c55e"
    c_red = "#b91c1c"         # Rejeição
    c_red_bg = "#fee2e2"
    c_red_border = "#ef4444"
    c_purple = "#6b21a8"      # Despacho SP156
    c_purple_bg = "#f5f3ff"
    c_purple_border = "#a855f7"

    # =========================================================================
    # CABEÇALHO COMPACTO
    # =========================================================================
    ax.text(119, 82.5, "PASSO SEGURO — FLUXO OPERACIONAL DE TRIAGEM RPA (BPMN 2.0)", 
            fontsize=13.0, fontweight="bold", ha="center", va="center", color="#0f172a")
    ax.text(119, 79.2, "Pipeline Horizontal Compacta: Higienização, Deduplicação, GeoSampa, IA e Despacho Diário", 
            fontsize=8.5, ha="center", va="center", color="#64748b")
    ax.plot([15, 223], [76.5, 76.5], color="#cbd5e1", lw=1.0)

    # Nível Y da esteira principal (Happy Path)
    cy = 46

    # =========================================================================
    # 1. INÍCIO DO PROCESSO (Esquerda)
    # =========================================================================
    start = patches.Circle((9, cy), 3.4, facecolor=c_green_bg, edgecolor=c_green_border, linewidth=2.4)
    ax.add_patch(start)
    ax.text(9, cy, "Início\nLote", fontsize=7.2, fontweight="bold", ha="center", va="center", color=c_green)
    ax.text(9, cy - 6.2, "Cron (30m) ou\nCLI Manual", fontsize=6.2, ha="center", va="top", color="#64748b")

    # Seta Início -> Tarefa 1
    ax.annotate("", xy=(16.5, cy), xytext=(12.5, cy), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # =========================================================================
    # 2. TAREFA 1: COLETAR RELATOS
    # =========================================================================
    t1 = patches.FancyBboxPatch((16.5, cy - 5.0), 24, 10, boxstyle="round,pad=0.4", 
                               facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.4)
    ax.add_patch(t1)
    ax.text(28.5, cy + 2.3, "1. Coletar Relatos", fontsize=7.5, fontweight="bold", ha="center", color=c_blue)
    ax.text(28.5, cy - 1.5, "GET /relatos?status=novo\n(API Central / Mock)", fontsize=6.2, ha="center", color="#1e3a8a")

    ax.annotate("", xy=(45.5, cy), xytext=(40.5, cy), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # =========================================================================
    # 3. TAREFA 2: VALIDAR MÍDIA & SANITIZAR LGPD
    # =========================================================================
    t2 = patches.FancyBboxPatch((45.5, cy - 5.0), 26.5, 10, boxstyle="round,pad=0.4", 
                               facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.4)
    ax.add_patch(t2)
    ax.text(58.7, cy + 2.3, "2. Validar Mídia & LGPD", fontsize=7.5, fontweight="bold", ha="center", color=c_blue)
    ax.text(58.7, cy - 1.5, "Pillow (Buffer Imagem) &\nRegex (Mascarar CPF/Tel)", fontsize=6.2, ha="center", color="#1e3a8a")

    ax.annotate("", xy=(76.5, cy), xytext=(72.0, cy), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # =========================================================================
    # 4. GATEWAY 1: FOTO ÍNTEGRA?
    # =========================================================================
    gw1 = patches.Polygon([[76.5, cy], [79.8, cy + 3.8], [83.1, cy], [79.8, cy - 3.8]], 
                          facecolor=c_amber_bg, edgecolor=c_amber_border, linewidth=1.4)
    ax.add_patch(gw1)
    ax.text(79.8, cy, "?", fontsize=8.5, fontweight="bold", ha="center", va="center", color=c_amber)
    ax.text(79.8, cy - 5.8, "GW1:\nFoto OK?", fontsize=6.2, fontweight="bold", ha="center", va="top", color=c_amber)

    # Ramo Não -> Sobe para Rejeição Foto
    ax.annotate("", xy=(79.8, cy + 15), xytext=(79.8, cy + 3.8), arrowprops=dict(arrowstyle="->", color=c_red, lw=1.6))
    ax.text(81.5, cy + 8.5, "[Não]", fontsize=6.5, fontweight="bold", color=c_red)

    t_rej1 = patches.FancyBboxPatch((68.8, cy + 15), 22, 7.5, boxstyle="round,pad=0.4", 
                                    facecolor=c_red_bg, edgecolor=c_red_border, linewidth=1.3)
    ax.add_patch(t_rej1)
    ax.text(79.8, cy + 19.8, "Rejeitar: Foto Inválida", fontsize=6.8, fontweight="bold", ha="center", color=c_red)
    ax.text(79.8, cy + 17.0, "PATCH status='rejeitado'", fontsize=5.8, ha="center", color="#7f1d1d")

    ax.annotate("", xy=(95.5, cy + 18.7), xytext=(90.8, cy + 18.7), arrowprops=dict(arrowstyle="->", color=c_red, lw=1.5))
    end_rej1 = patches.Circle((98.0, cy + 18.7), 2.3, facecolor=c_red_bg, edgecolor=c_red_border, linewidth=2.0)
    ax.add_patch(end_rej1)
    ax.text(98.0, cy + 18.7, "Fim", fontsize=5.8, fontweight="bold", ha="center", va="center", color=c_red)

    # Ramo Sim -> Segue para Tarefa 3
    ax.annotate("", xy=(88.0, cy), xytext=(83.1, cy), arrowprops=dict(arrowstyle="->", color=c_green, lw=1.8))
    ax.text(85.2, cy + 2.0, "[Sim]", fontsize=6.5, fontweight="bold", color=c_green)

    # =========================================================================
    # 5. TAREFA 3: LIMITES TERRITORIAIS & DEDUPLICAÇÃO
    # =========================================================================
    t3 = patches.FancyBboxPatch((88.0, cy - 5.0), 26.5, 10, boxstyle="round,pad=0.4", 
                               facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.4)
    ax.add_patch(t3)
    ax.text(101.2, cy + 2.3, "3. Checar SP & Duplicata", fontsize=7.5, fontweight="bold", ha="center", color=c_blue)
    ax.text(101.2, cy - 1.5, "Bounding Box da Capital &\nHaversine (<= 30m / 14d)", fontsize=6.2, ha="center", color="#1e3a8a")

    ax.annotate("", xy=(119.0, cy), xytext=(114.5, cy), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # =========================================================================
    # 6. GATEWAY 2: EM SP & INÉDITO?
    # =========================================================================
    gw2 = patches.Polygon([[119.0, cy], [122.3, cy + 3.8], [125.6, cy], [122.3, cy - 3.8]], 
                          facecolor=c_amber_bg, edgecolor=c_amber_border, linewidth=1.4)
    ax.add_patch(gw2)
    ax.text(122.3, cy, "?", fontsize=8.5, fontweight="bold", ha="center", va="center", color=c_amber)
    ax.text(122.3, cy - 5.8, "GW2:\nVálido?", fontsize=6.2, fontweight="bold", ha="center", va="top", color=c_amber)

    # Ramo Não -> Sobe para Rejeição Territorial / Duplicidade
    ax.annotate("", xy=(122.3, cy + 15), xytext=(122.3, cy + 3.8), arrowprops=dict(arrowstyle="->", color=c_red, lw=1.6))
    ax.text(124.0, cy + 8.5, "[Não]", fontsize=6.5, fontweight="bold", color=c_red)

    t_rej2 = patches.FancyBboxPatch((111.3, cy + 15), 22, 7.5, boxstyle="round,pad=0.4", 
                                    facecolor=c_red_bg, edgecolor=c_red_border, linewidth=1.3)
    ax.add_patch(t_rej2)
    ax.text(122.3, cy + 19.8, "Rejeitar: Fora SP/Duplicado", fontsize=6.6, fontweight="bold", ha="center", color=c_red)
    ax.text(122.3, cy + 17.0, "PATCH status='rejeitado'", fontsize=5.8, ha="center", color="#7f1d1d")

    ax.annotate("", xy=(138.0, cy + 18.7), xytext=(133.3, cy + 18.7), arrowprops=dict(arrowstyle="->", color=c_red, lw=1.5))
    end_rej2 = patches.Circle((140.5, cy + 18.7), 2.3, facecolor=c_red_bg, edgecolor=c_red_border, linewidth=2.0)
    ax.add_patch(end_rej2)
    ax.text(140.5, cy + 18.7, "Fim", fontsize=5.8, fontweight="bold", ha="center", va="center", color=c_red)

    # Ramo Sim -> Segue para Tarefa 4 (GeoSampa & IA)
    ax.annotate("", xy=(130.5, cy), xytext=(125.6, cy), arrowprops=dict(arrowstyle="->", color=c_green, lw=1.8))
    ax.text(127.7, cy + 2.0, "[Sim]", fontsize=6.5, fontweight="bold", color=c_green)

    # =========================================================================
    # 7. TAREFA 4: GEOSAMPA & VISÃO COMPUTACIONAL (IA)
    # =========================================================================
    t4 = patches.FancyBboxPatch((130.5, cy - 5.0), 26.5, 10, boxstyle="round,pad=0.4", 
                               facecolor=c_light_blue, edgecolor=c_blue_border, linewidth=1.4)
    ax.add_patch(t4)
    ax.text(143.7, cy + 2.3, "4. GeoSampa & Visão IA", fontsize=7.5, fontweight="bold", ha="center", color=c_blue)
    ax.text(143.7, cy - 1.5, "Point-in-Polygon (32 Subprefs) &\nMicrosserviço YOLOv8", fontsize=6.2, ha="center", color="#1e3a8a")

    ax.annotate("", xy=(161.5, cy), xytext=(157.0, cy), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.8))

    # =========================================================================
    # 8. GATEWAY 3: CONFIANÇA IA >= 0.60?
    # =========================================================================
    gw3 = patches.Polygon([[161.5, cy], [164.8, cy + 3.8], [168.1, cy], [164.8, cy - 3.8]], 
                          facecolor=c_amber_bg, edgecolor=c_amber_border, linewidth=1.4)
    ax.add_patch(gw3)
    ax.text(164.8, cy, "?", fontsize=8.5, fontweight="bold", ha="center", va="center", color=c_amber)
    ax.text(164.8, cy + 5.8, "GW3:\nConfiança\n>= 0.60?", fontsize=6.2, fontweight="bold", ha="center", va="bottom", color=c_amber)

    # Ramo Não (< 0.60) -> Desce para Fila de Revisão Humana
    ax.annotate("", xy=(164.8, cy - 15), xytext=(164.8, cy - 3.8), arrowprops=dict(arrowstyle="->", color=c_amber, lw=1.6))
    ax.text(166.5, cy - 8.5, "[< 0.60]", fontsize=6.5, fontweight="bold", color=c_amber)

    t_rev = patches.FancyBboxPatch((153.8, cy - 22.5), 22, 7.5, boxstyle="round,pad=0.4", 
                                   facecolor=c_amber_bg, edgecolor=c_amber_border, linewidth=1.3)
    ax.add_patch(t_rev)
    ax.text(164.8, cy - 17.7, "Fila de Revisão Humana", fontsize=6.8, fontweight="bold", ha="center", color=c_amber)
    ax.text(164.8, cy - 20.5, "PATCH status='revisao_humana'", fontsize=5.8, ha="center", color="#854d0e")

    ax.annotate("", xy=(180.5, cy - 18.7), xytext=(175.8, cy - 18.7), arrowprops=dict(arrowstyle="->", color=c_amber, lw=1.5))
    end_rev = patches.Circle((183.0, cy - 18.7), 2.3, facecolor=c_amber_bg, edgecolor=c_amber_border, linewidth=2.0)
    ax.add_patch(end_rev)
    ax.text(183.0, cy - 18.7, "Fim", fontsize=5.8, fontweight="bold", ha="center", va="center", color=c_amber)

    # Ramo Sim -> Segue para Tarefa 5 (Infosiga & Status)
    ax.annotate("", xy=(173.0, cy), xytext=(168.1, cy), arrowprops=dict(arrowstyle="->", color=c_green, lw=1.8))
    ax.text(170.2, cy + 2.0, "[Sim]", fontsize=6.5, fontweight="bold", color=c_green)

    # =========================================================================
    # 9. TAREFA 5: RISCO INFOSIGA & ATUALIZAÇÃO API
    # =========================================================================
    t5 = patches.FancyBboxPatch((173.0, cy - 5.0), 25.5, 10, boxstyle="round,pad=0.4", 
                               facecolor=c_green_bg, edgecolor=c_green_border, linewidth=1.4)
    ax.add_patch(t5)
    ax.text(185.7, cy + 2.3, "5. Risco Infosiga & Status", fontsize=7.5, fontweight="bold", ha="center", color=c_green)
    ax.text(185.7, cy - 1.5, "Cruzamento Sinistros Fatais &\nPATCH status='encaminhado'", fontsize=6.2, ha="center", color="#14532d")

    ax.annotate("", xy=(203.0, cy), xytext=(198.5, cy), arrowprops=dict(arrowstyle="->", color=c_purple, lw=1.8))

    # =========================================================================
    # 10. TAREFA 6: DESPACHO SP156 & AUDITORIA
    # =========================================================================
    t6 = patches.FancyBboxPatch((203.0, cy - 5.8), 22.0, 11.6, boxstyle="round,pad=0.5", 
                               facecolor=c_purple_bg, edgecolor=c_purple_border, linewidth=1.5)
    ax.add_patch(t6)
    ax.text(214.0, cy + 2.8, "6. Despacho & Logs", fontsize=7.5, fontweight="bold", ha="center", color=c_purple)
    ax.text(214.0, cy - 2.8, "• Pacotes SP156 (CSV/PDF)\n• Auditoria JSONL (SHA-256)", 
            fontsize=6.0, ha="center", color="#581c87")

    # Seta Final -> Evento Fim
    ax.annotate("", xy=(228.5, cy), xytext=(225.0, cy), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=2.0))

    # =========================================================================
    # 11. EVENTO FIM DO LOTE (Direita)
    # =========================================================================
    end_outer = patches.Circle((231.5, cy), 3.0, facecolor="#e2e8f0", edgecolor="#0f172a", linewidth=2.4)
    end_inner = patches.Circle((231.5, cy), 2.0, facecolor="#0f172a", edgecolor="#0f172a", linewidth=1.0)
    ax.add_patch(end_outer)
    ax.add_patch(end_inner)
    ax.text(231.5, cy, "FIM", fontsize=6.2, fontweight="bold", ha="center", va="center", color="#ffffff")
    ax.text(231.5, cy - 5.8, "Fim do\nLote", fontsize=6.2, fontweight="bold", ha="center", va="top", color="#0f172a")

    plt.tight_layout()
    
    docs_png = Path("docs/triagem_processo.png")
    docs_png.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(docs_png, dpi=260, bbox_inches="tight")
    plt.close(fig)
    print(f"Diagrama BPMN 2.0 horizontal gerado com sucesso em {docs_png}")


if __name__ == "__main__":
    desenhar_diagrama()
