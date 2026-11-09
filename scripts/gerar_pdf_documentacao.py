import os
from pathlib import Path
from fpdf import FPDF


def clean_str(texto: str) -> str:
    """Substitui caracteres especiais fora do latin-1 padrão."""
    if not texto:
        return ""
    replacements = {
        "—": "-", "–": "-", "“": '"', "”": '"', "’": "'", "‘": "'",
        "•": "*", "→": "->", "➔": "->", "≥": ">=", "≤": "<=", "°": "o"
    }
    for orig, rep in replacements.items():
        texto = texto.replace(orig, rep)
    return texto.encode("latin-1", "replace").decode("latin-1")


class DocumentacaoPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 5, clean_str("Passo Seguro — Módulo de Automação (RPA & Triagem) | FIAP Global Solution 2026"), 
                      border=0, new_x="LMARGIN", new_y="NEXT", align="L")
            self.set_draw_color(226, 232, 240)
            self.line(10, 16, 200, 16)
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, clean_str(f"Pagina {self.page_no()} | Documento de Entrega Oficial - Equipe Passo Seguro"), align="C")

    def chapter_title(self, num: str, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 64, 175) # Azul marinho FIAP
        self.cell(0, 8, clean_str(f"{num}. {title}"), new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_draw_color(37, 99, 235)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(15, 23, 42)
        self.cell(0, 6, clean_str(title), new_x="LMARGIN", new_y="NEXT", align="L")
        self.ln(1)

    def body_p(self, text: str):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(51, 65, 85)
        self.multi_cell(0, 4.8, clean_str(text))
        self.ln(2.5)

    def bullet_point(self, label: str, text: str):
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(30, 41, 59)
        self.write(4.8, clean_str(f"* {label}: "))
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(51, 65, 85)
        self.write(4.8, clean_str(text + "\n"))


def gerar_pdf_entrega():
    pdf = DocumentacaoPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    
    # ------------------ PÁGINA 1: CAPA & SUMÁRIO EXECUTIVO ------------------
    pdf.add_page()
    pdf.ln(15)
    
    # Faixa decorativa superior
    pdf.set_fill_color(30, 64, 175)
    pdf.rect(10, 20, 190, 6, "F")
    
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, clean_str("PASSO SEGURO"), new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 8, clean_str("CitizenTech para Segurança de Pedestres e Zeladoria Urbana"), new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, clean_str("Módulo de Automação Operacional (RPA & Triagem em Lote)"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 6, clean_str("FIAP — Global Solution 2026 | Engenharia de Software"), new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.ln(15)
    
    # Box de Integrantes
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(15, 78, 180, 48, "DF")
    
    pdf.set_xy(20, 83)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, clean_str("EQUIPE DO PROJETO:"), new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(51, 65, 85)
    pdf.set_x(20)
    pdf.write(5.5, clean_str("• Guilherme Morais — RM 551981 (Responsável Técnico pelo Módulo de Automação/RPA)\n"))
    pdf.set_x(20)
    pdf.write(5.5, clean_str("• Júlia Marques — RM 98680 (Equipe Passo Seguro)\n"))
    pdf.set_x(20)
    pdf.write(5.5, clean_str("• Matheus Gusmão — RM 550826 (Equipe Passo Seguro)\n\n"))
    
    pdf.set_x(20)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.write(5.5, clean_str("Links Oficiais de Entrega:\n"))
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 9)
    pdf.write(5.5, clean_str("• Repositório do Módulo RPA: https://github.com/Passo-Seguro/passo-seguro-rpa\n"))
    pdf.set_x(20)
    pdf.write(5.5, clean_str("• Vídeo de Demonstração (3 min): https://youtu.be/passo-seguro-rpa-demo (disponível no README)\n"))
    
    pdf.ln(25)
    
    # Sumário Executivo
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(0, 7, clean_str("Sumário Executivo da Solução"), new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.body_p(
        "O Passo Seguro é uma plataforma de CitizenTech desenhada para empoderar a população de São Paulo "
        "na identificação, notificação e acompanhamento de problemas críticos em calçadas (buracos, desníveis, "
        "obstruções ilegais de veículos e rampas de acessibilidade bloqueadas). "
        "Dentro da arquitetura do MVP, o módulo de Robotic Process Automation (RPA / Triagem) atua como o motor "
        "central de higienização, deduplicação e triagem operacional em lote, aliviando o gargalo crônico de análise "
        "manual da administração pública municipal e viabilizando o despacho direto para as 32 Subprefeituras da capital."
    )
    
    # ------------------ PÁGINA 2: DIAGNÓSTICO DO PROBLEMA & ARQUITETURA ------------------
    pdf.add_page()
    pdf.chapter_title("1", "CitizenTech, Problema e Benefício ao Cidadão")
    
    pdf.section_title("1.1 O Diagnóstico das Calçadas em São Paulo")
    pdf.body_p(
        "A cidade de São Paulo possui mais de 34 mil quilômetros de calçadas, das quais estima-se que mais de 60% "
        "apresentem inconformidades com as normas de acessibilidade (NBR 9050). O resultado desse cenário é alarmante: "
        "quedas diárias de idosos, bloqueio completo de locomoção para pessoas com deficiência física e o empurrão involuntário "
        "de pedestres para o leito viário, gerando atropelamentos graves."
    )
    
    pdf.section_title("1.2 O Gargalo da Triagem e o Papel do RPA")
    pdf.body_p(
        "Canais tradicionais de zeladoria urbana, como o SP156, recebem dezenas de milhares de chamados mensais sem qualquer "
        "higienização prévia. Isso acarreta relatos duplicados para o mesmo buraco, imagens corrompidas ou impróprias, "
        "coordenadas fora da jurisdição municipal e total ausência de critérios objetivos de prioridade baseados em risco de vida. "
        "A automação robótica do Passo Seguro atua imediatamente após a coleta de novos relatos, aplicando filtros espaciais, "
        "sanitização conforme a LGPD e cálculo automático de criticidade antes de despachar pacotes estruturados aos órgãos competentes."
    )
    
    pdf.chapter_title("2", "Objetivo da Automação e Ciclo de Vida do Relato")
    pdf.body_p(
        "A automação tem como missão primordial operar de forma autônoma e programada (agendamento a cada 30 minutos) "
        "ou sob demanda via CLI. O robô consome relatos com status 'novo', executa validações rigorosas e atualiza o estado "
        "do chamado no banco de dados e no PWA do cidadão."
    )
    
    pdf.bullet_point("novo -> rejeitado", "Descarte quando a foto está corrompida, as coordenadas estão fora do município de SP ou quando há duplicidade geográfica detectada.")
    pdf.bullet_point("novo -> revisao_humana", "Acionado quando a classificação por visão computacional possui índice de confiança inferior a 60% (0.60).")
    pdf.bullet_point("novo -> encaminhado", "Relato íntegro, classificado com Prioridade ALTA, NORMAL ou BAIXA, enriquecido com dados de Subprefeitura e pronto para despacho municipal.")
    
    pdf.ln(3)
    
    # ------------------ PÁGINA 3: DESENHO DO PROCESSO (BPMN) ------------------
    pdf.add_page()
    pdf.chapter_title("3", "Desenho do Processo e Fluxo Operacional (BPMN 2.0)")
    
    pdf.body_p(
        "A esteira foi modelada seguindo o padrão BPMN 2.0 internacional, incorporando isolamento de falha item a item "
        "e dois gateways lógicos de decisão (confiança visual e matriz de risco Infosiga):"
    )
    
    # Inserção da imagem do diagrama BPMN
    img_path = Path("docs/triagem_processo.png")
    if img_path.exists():
        pdf.image(str(img_path), x=12, y=pdf.get_y(), w=186)
        pdf.ln(112)
    
    pdf.section_title("3.1 Detalhamento das Etapas da Pipeline")
    pdf.bullet_point("Etapa 1 - Coleta", "Consumo páginado da rota GET /relatos?status=novo com política de retentativa exponencial.")
    pdf.bullet_point("Etapa 2 - Validação de Mídia", "Decodificação de buffer binário e validação de dimensões mínimas com Pillow.")
    pdf.bullet_point("Etapa 3 - Limite Territorial", "Bounding Box aproximada de São Paulo (Lat: -24.0 a -23.3, Lon: -46.9 a -46.3).")
    pdf.bullet_point("Etapa 4 - Deduplicação", "Cálculo de Haversine: se houver avaria idêntica em raio <= 30m nos últimos 14 dias, rejeita por duplicidade.")
    pdf.bullet_point("Etapa 5 - GeoSampa", "Enriquecimento via Point-in-Polygon determinando a Subprefeitura e Distrito administrativo.")
    pdf.bullet_point("Gateway 1 (Visão)", "Se acurácia < 0.60, desvia para revisao_humana.")
    pdf.bullet_point("Gateway 2 (Infosiga)", "Cruzamento com histórico de atropelamentos fatais/graves (raio 150m) e classe de dano, definindo prioridade ALTA.")
    pdf.bullet_point("Etapa 6 - Despacho SP156", "Exportação automática de CSVs estruturados e relatórios PDF por Subprefeitura em dist/pacotes/.")
    pdf.bullet_point("Etapa 7 - Auditoria", "Registro de eventos em logs/execucao_amostra.jsonl anonimizados conforme a LGPD.")
    
    # ------------------ PÁGINA 4: TECNOLOGIAS, EXCEÇÕES & LGPD ------------------
    pdf.add_page()
    pdf.chapter_title("4", "Tecnologias Utilizadas e Justificativa Técnica")
    
    pdf.bullet_point("Python 3.12", "Linguagem nativa com ecossistema líder em análise espacial, manipulação de dados e automação de scripts.")
    pdf.bullet_point("Shapely & GeoJSON", "Biblioteca de alta performance geométrica utilizada no algoritmo Point-in-Polygon com os polígonos oficiais do GeoSampa.")
    pdf.bullet_point("Tenacity", "Biblioteca para resiliência de rede através de Exponential Backoff progressivo (1s, 2s, 4s) com tratamento gracioso de HTTP 503.")
    pdf.bullet_point("Pillow (PIL)", "Verificação estrita e sem vulnerabilidades de buffers de imagem JPEG/PNG, evitando injeções de arquivos corrompidos.")
    pdf.bullet_point("FPDF2", "Geração ágil e autônoma de relatórios operacionais em PDF sem necessidade de dependências binárias pesadas de sistema operacional.")
    pdf.bullet_point("Pytest & Responses", "Harness completo de testes unitários e de integração simulando respostas das APIs de backend e visão computacional.")
    pdf.bullet_point("Docker & Docker Compose", "Padronização para execução contínua em servidor local, esteira de CI/CD ou agendamentos cron corporativos.")
    
    pdf.chapter_title("5", "Tratamento de Exceções, Resiliência e LGPD")
    
    pdf.section_title("5.1 Resiliência com Isolamento de Falha")
    pdf.body_p(
        "Em ambiente de produção de automação (RPA), um dos princípios arquiteturais fundamentais é que a falha em um "
        "registro isolado nunca deve derrubar o processamento do lote como um todo. A esteira implementa laço iterativo protegido "
        "com try/except por item. Caso um relato apresente payload corrompido ou gere erro de conexão não previsto, a ocorrência "
        "é registrada em auditoria e o processamento prossegue normalmente com os próximos itens."
    )
    pdf.body_p(
        "Para a comunicação com os microsserviços externos (API Central e Serviço de Visão YOLO), o cliente HTTP "
        "utiliza decoradores de retentativa automática (tenacity). Se a API de visão computacional estiver fora do ar "
        "(ex.: HTTP 503 Service Unavailable), o robô executa 3 tentativas progressivas e, caso persista indisponível, "
        "realiza degradação suave (fallback), evitando travar a triagem."
    )
    
    pdf.section_title("5.2 Segurança e Privacidade de Dados (LGPD)")
    pdf.body_p(
        "Em total respeito à Lei Geral de Proteção de Dados (Lei 13.709/2018):"
    )
    pdf.bullet_point("Sanitização por Regex", "Números de CPF e telefones informados pelos cidadãos são imediatamente mascarados nos textos (***.***.***-** e (**) *****-****).")
    pdf.bullet_point("Logs Anonimizados", "Nenhuma foto binária, texto livre de usuário ou coordenada decimal aberta é gravada em logs. Os registros utilizam hash SHA-256 do identificador do chamado.")
    pdf.bullet_point("Despacho Minimizado", "Os arquivos enviados aos canais da Prefeitura contêm apenas as informações estritamente necessárias para a zeladoria da calçada.")
    
    # ------------------ PÁGINA 5: TESTES AUTOMATIZADOS & ROTEIRO DO VÍDEO ------------------
    pdf.add_page()
    pdf.chapter_title("6", "Validação e Testes Automatizados (Pytest)")
    
    pdf.body_p(
        "A esteira conta com 18 testes automatizados implementados com pytest e responses, garantindo 100% de conformidade "
        "com os requisitos funcionais e de resiliência:"
    )
    
    # Tabela de Testes
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(50, 7, clean_str("Módulo de Teste"), border=1, fill=True)
    pdf.cell(35, 7, clean_str("Cenário Avaliado"), border=1, fill=True)
    pdf.cell(105, 7, clean_str("Comportamento Esperado Validado"), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 8)
    linhas_tabela = [
        ("test_validacao.py", "Foto Íntegra vs Inválida", "Aceita base64 válido e rejeita buffers corrompidos ou vazios."),
        ("test_validacao.py", "Bounding Box SP", "Aprova coordenadas da capital e rejeita pontos no litoral/outros estados."),
        ("test_validacao.py", "Sanitização LGPD", "Aplica regex ofuscando CPFs e telefones em formulários e logs."),
        ("test_deduplicacao.py", "Haversine & Janela", "Rejeita chamados a menos de 30m em 14 dias; tolera tipos diferentes."),
        ("test_prioridade.py", "Gateway 1 (Visão)", "Confiança < 0.60 desvia o chamado para status 'revisao_humana'."),
        ("test_prioridade.py", "Gateway 2 (Infosiga)", "Coordenada próxima a sinistro fatal eleva prioridade para 'ALTA'."),
        ("test_resiliencia_api.py", "Serviço Visão 503", "Executa 3 tentativas com backoff e degrada suavemente sem exceção."),
        ("test_pipeline_integracao.py", "Lote Demo 10 Relatos", "Processa o lote completo gerando pacotes CSV e relatórios PDF.")
    ]
    
    for mod, cen, comp in linhas_tabela:
        pdf.cell(50, 6, clean_str(mod), border=1)
        pdf.cell(35, 6, clean_str(cen), border=1)
        pdf.cell(105, 6, clean_str(comp), border=1, new_x="LMARGIN", new_y="NEXT")
        
    pdf.ln(5)
    pdf.chapter_title("7", "Roteiro Operacional do Vídeo de Demonstração (Até 3 Minutos)")
    
    pdf.body_p(
        "Para a gravação do pitch em vídeo do componente de Automação, o roteiro estruturado segue os tempos determinados:"
    )
    
    pdf.bullet_point("0:00 - 0:30 | Introdução", "Apresentação dos integrantes e contextualização do problema de zeladoria de calçadas em SP.")
    pdf.bullet_point("0:30 - 1:30 | Execução Ao Vivo", "Execução do comando 'python -m src.triagem.main --executar-uma-vez --mock-data tests/fixtures/lote_demo.json', destacando o descarte da imagem corrompida, o descarte do relato duplicado a 7.5m e a identificação de área com sinistro fatal do Infosiga.")
    pdf.bullet_point("1:30 - 2:15 | Entregáveis Gerados", "Abertura dos logs JSONL em logs/execucao_amostra.jsonl e demonstração do CSV e relatório PDF gerados para a Subprefeitura da Sé em dist/pacotes/.")
    pdf.bullet_point("2:15 - 2:45 | Resiliência", "Execução de 'pytest tests/ -v' demonstrando os 18 testes passando e explicação das 3 retentativas automáticas com Exponential Backoff.")
    pdf.bullet_point("2:45 - 3:00 | Conclusão", "Fechamento evidenciando a mudança de status no PWA do cidadão e a entrega dos despachos municipais.")
    
    pdf.ln(5)
    pdf.set_fill_color(220, 252, 231)
    pdf.set_draw_color(22, 163, 74)
    pdf.rect(10, pdf.get_y(), 190, 18, "DF")
    pdf.set_xy(15, pdf.get_y() + 3)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(20, 83, 45)
    pdf.cell(0, 5, clean_str("STATUS DA ENTREGA: PROTÓTIPO VALIDADO E DOCUMENTADO"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(0, 5, clean_str("Todos os artefatos de código, testes, BPMN e relatórios estão integrados e disponíveis no repositório."), new_x="LMARGIN", new_y="NEXT")
    
    caminho_final = Path("dist/entrega_passo_seguro_rpa.pdf")
    caminho_final.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(caminho_final))
    print(f"Documento de entrega oficial gerado com sucesso em: {caminho_final}")


if __name__ == "__main__":
    gerar_pdf_entrega()
