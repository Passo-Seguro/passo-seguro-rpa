# Passo Seguro — Robotic Process Automation (RPA & Triagem)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Testes](https://img.shields.io/badge/Pytest-18%20passed-brightgreen.svg)]()
[![LGPD](https://img.shields.io/badge/LGPD-Compliant-success.svg)]()
[![Status](https://img.shields.io/badge/Status-Protótipo%20Validado-orange.svg)]()

Ficha Técnica Geral: [README do repositório principal](https://github.com/Passo-Seguro/passo-seguro#ficha-técnica)

---

## 👥 Integrantes

| Nome completo | RM | Papel no Projeto |
|---|---|---|
| **Guilherme Morais** | **551981** | **Responsável Técnico pelo Módulo de Automação (RPA)** |
| Júlia Marques | 98680 | Equipe Passo Seguro |
| Matheus Gusmão | 550826 | Equipe Passo Seguro |

### 🔗 Repositórios do Ecossistema
* Principal: [passo-seguro](https://github.com/Passo-Seguro/passo-seguro)
* GenAI: [passo-seguro-genai](https://github.com/Passo-Seguro/passo-seguro-genai)
* Dados: [passo-seguro-dados](https://github.com/Passo-Seguro/passo-seguro-dados)
* Visão: [passo-seguro-visao](https://github.com/Passo-Seguro/passo-seguro-visao)
* **RPA (este repositório): [passo-seguro-rpa](https://github.com/Passo-Seguro/passo-seguro-rpa)**
* Robô: [passo-seguro-robo](https://github.com/Passo-Seguro/passo-seguro-robo)

---

## 🎯 Objetivo e Papel da Automação

No projeto **Passo Seguro** (solução de CitizenTech para segurança de pedestres e zeladoria urbana no município de São Paulo), a automação (RPA) atua como o **orquestrador operacional de triagem em lote**. 

O robô consome relatos enviados por cidadãos via aplicativo, valida a integridade da mídia, sanitiza dados pessoais (LGPD), descarta relatos duplicados por proximidade geográfica e temporal, enriquece a localização com as Subprefeituras de São Paulo (GeoSampa) e calcula a prioridade de atendimento cruzando as ocorrências com o histórico de sinistros fatais e graves de atropelamento (Infosiga). Ao término, gera os pacotes diários de despacho para o canal municipal SP156 (em formatos CSV e PDF) e atualiza a API central.

### Ciclo de Vida do Status do Relato
$$\text{novo} \longrightarrow \begin{cases} \textbf{revisao\_humana} & \text{(se confiança visual } < 0.60\text{)} \\ \textbf{rejeitado} & \text{(foto corrompida, fora de SP ou duplicado)} \\ \textbf{validado} \longrightarrow \textbf{encaminhado} & \text{(Prioridade ALTA / NORMAL / BAIXA)} \end{cases}$$

---

## 🏗️ Estrutura do Repositório

```plaintext
passo-seguro-rpa/
├── docs/
│   ├── especificacao_rpa.md      # Especificação completa importada do Gemini
│   ├── triagem_processo.bpmn     # Diagrama BPMN da esteira de triagem
│   └── triagem_processo.png      # Export visual do diagrama de processo (BPMN 2.0)
├── src/
│   └── triagem/
│       ├── __init__.py
│       ├── config.py             # Configurações Pydantic Settings e Bounding Box SP
│       ├── cliente_api.py        # Clientes HTTP com resiliência e Exponential Backoff
│       ├── validacao.py          # Checagem de imagem (Pillow), limites SP e regex LGPD
│       ├── deduplicacao.py       # Algoritmo de Haversine (30m) e janela de 14 dias
│       ├── geo.py                # Point-in-polygon com GeoJSON das 32 subprefeituras
│       ├── prioridade.py         # Matriz de prioridade (tipo de dano + dados Infosiga)
│       ├── pacote.py             # Compilação e exportação de CSV e relatórios PDF SP156
│       └── main.py               # Orquestrador CLI (--executar-uma-vez, logs JSONL)
├── scripts/
│   ├── render_bpmn_diagram.py    # Gerador visual do fluxo BPMN em alta resolução
│   └── gerar_pdf_documentacao.py # Compilador do documento oficial de entrega acadêmica
├── data/
│   ├── geosampa_subprefeituras.geojson   # Polígonos das subprefeituras e distritos
│   └── infosiga_sinistros_mock.csv       # Histórico de atropelamentos críticos
├── dist/
│   ├── entrega_passo_seguro_rpa.pdf     # Documento oficial de entrega (Teams)
│   └── pacotes/                  # Arquivos CSV e relatórios PDF gerados por subprefeitura
├── assets/
│   └── triagem_processo.png      # Evidências visuais e diagrama de arquitetura
├── logs/
│   ├── execucao_amostra.jsonl    # Amostra de logs estruturados e sanitizados
│   └── triagem_YYYY-MM-DD.log    # Logs diários de auditoria
├── tests/
│   ├── fixtures/
│   │   └── lote_demo.json        # 10 relatos de teste cobrindo todos os cenários da esteira
│   ├── conftest.py
│   ├── test_validacao.py
│   ├── test_deduplicacao.py
│   ├── test_prioridade.py
│   ├── test_resiliencia_api.py   # Testes de falha 503, retry e degradação suave
│   └── test_pipeline_integracao.py
├── Dockerfile                    # Container pronto para agendamento ou execução sob demanda
├── docker-compose.yml            # Orquestração local dos serviços
├── pytest.ini                    # Configuração de paths dos testes automatizados
├── requirements.txt              # Dependências do projeto
└── README.md
```

---

## ⚙️ Instalação e Execução Local

### 1. Pré-requisitos
* Python 3.10+ (recomendado 3.12)
* Git instalado

### 2. Configuração do Ambiente Virtual
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# No Linux / macOS:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Execução sob Demanda (Demonstração com Mocks)
Comando oficial para demonstração da esteira completa em lote:
```bash
python -m src.triagem.main --executar-uma-vez --mock-data tests/fixtures/lote_demo.json
```

### 4. Execução Contínua em Agendamento (a cada 30 minutos)
```bash
python -m src.triagem.main --intervalo 30
```

### 5. Execução via Docker Compose
```bash
# Rodar execução da demonstração em container
docker compose run --rm triagem-demo

# Ou iniciar o serviço contínuo agendado
docker compose up -d triagem
```

---

## 🧪 Testes Automatizados

O projeto conta com suíte de testes automatizados com cobertura total dos módulos da esteira:

```bash
pytest tests/ -v
```

**Cenários validados nos testes:**
* `test_validacao.py`: Validação de imagem íntegra vs corrompida, coordenadas dentro vs fora da capital, e expressões regulares de mascaramento LGPD (CPF e telefone).
* `test_deduplicacao.py`: Cálculo da distância geodésica de Haversine, descarte por duplicidade em raio $\le 30$ metros / 14 dias, e tolerância a avarias de tipos distintos.
* `test_prioridade.py`: Gateway 1 (desvio para `revisao_humana` em casos de baixa acurácia do modelo visual) e Gateway 2 (elevação para `ALTA` prioridade em raios de sinistros fatais do Infosiga).
* `test_resiliencia_api.py`: Simulação com `responses` de falha HTTP 503 na API de visão e API principal, comprovando as 3 tentativas com Exponential Backoff e degradação suave.
* `test_pipeline_integracao.py`: Execução ponta a ponta do lote demonstrativo com verificação das métricas e geração dos arquivos CSV e PDF.

---

## 🛡️ Segurança e Privacidade (LGPD)

Em estrita conformidade com a Lei Geral de Proteção de Dados (LGPD):
1. **Sanitização de Dados:** Expressões regulares ofuscam números de CPF (`***.***.***-**`) e telefones (`(**) *****-****`) de descrições e formulários.
2. **Logs Anonimizados:** Os arquivos de log (`logs/execucao_amostra.jsonl`) registram apenas o hash SHA-256 do identificador do relato, o status e a etapa. Nunca são persistidas fotos binárias, descrições em texto puro ou coordenadas geográficas exatas nos logs de auditoria.
3. **Relatórios Limpos:** Os pacotes de despacho enviados às Subprefeituras contêm apenas dados anonimizados estritamente necessários para a execução da zeladoria.

---

## 📹 Roteiro Sugerido para Vídeo de Demonstração (Até 3 Minutos)

| Tempo | Etapa do Vídeo | O que demonstrar em tela |
|---|---|---|
| **0:00 - 0:30** | **Apresentação e Problema** | Apresentar os integrantes e explicar o gargalo de triagem manual dos chamados de calçadas de SP. |
| **0:30 - 1:30** | **Execução ao Vivo do Lote** | Executar no terminal: `python -m src.triagem.main --executar-uma-vez --mock-data tests/fixtures/lote_demo.json`. Destacar o descarte da foto corrompida, o descarte por duplicidade (7.5m) e a detecção de área de sinistro fatal na Sé. |
| **1:30 - 2:15** | **Logs e Entregáveis Gerados** | Abrir o arquivo de log JSONL (`logs/execucao_amostra.jsonl`) demonstrando a sanitização LGPD. Abrir a pasta `dist/pacotes/` e exibir os arquivos CSV e PDF gerados para a Subprefeitura da Sé. |
| **2:15 - 2:45** | **Resiliência e Testes** | Executar `pytest tests/ -v` comprovando os 18 testes passando e demonstrar o teste de resiliência (`test_resiliencia_api.py`) com simulação de 503 e 3 retentativas automáticas (`tenacity`). |
| **2:45 - 3:00** | **Conclusão e Próximos Passos** | Exibir a integração planejada com o PWA do Passo Seguro e encerramento. |
