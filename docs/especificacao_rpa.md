# Especificação de Automação Passo Seguro

## Resposta do Gemini:

Aqui está a especificação completa, estruturada e detalhada do módulo de
Automação (RPA / Triagem)
do projeto
Passo Seguro
. Este documento foi desenhado no formato de
Contexto e Instruções Técnicas de Implementação
, pronto para ser repassado diretamente para agentes de IA (como Antigravity / Cursor / Copilot) ou desenvolvedores iniciarem o protótipo contra
mocks
de forma independente
.
CONTEXT & SPECIFICATION PROMPT: PASSO SEGURO — RPA & TRIAGEM
1. Visão Geral e Contexto de Negócio
Projeto:
Passo Seguro (CitizenTech para zeladoria colaborativa e segurança de pedestres em São Paulo)
.
Repositório do componente:
passo-seguro-rpa
.
Responsável:
Guilherme Morais (RM 551981) | Equipe: Júlia Marques (RM 98680), Matheus Gusmão (RM 550826)
.
Papel da Automação no MVP:
Atuar como o orquestrador de triagem operacional em lote
. O robô coleta novos relatos de calçadas danificadas/obstruídas, aplica regras de validação (sanitização LGPD e integridade de mídia), deduplica chamados em um raio geográfico, enriquece com dados territoriais (GeoSampa), calcula prioridade com dados de sinistros (Infosiga) e gera os pacotes diários de despacho por subprefeitura, atualizando os status na API principal
.
Ciclo de Vida do Status do Relato:
novo
➔
revisao_humana
(se confiança baixa) ➔
validado
➔
encaminhado
(ou
rejeitado
)
.
2. Estrutura do Repositório (
passo-seguro-rpa
)
Conforme o padrão de entregáveis exigido
, a estrutura de pastas e arquivos deve seguir rigorosamente:
Plaintext
passo-seguro-rpa/
├── docs/
│   ├── triagem_processo.bpmn     # Diagrama exportado via bpmn.io / Camunda
│   └── triagem_processo.png      # Render visual do fluxo BPMN
├── src/
│   └── triagem/
│       ├── __init__.py
│       ├── config.py             # Configurações via pydantic-settings / env vars
│       ├── cliente_api.py        # Clientes HTTP (API Passo Seguro e Visão) com retentativas
│       ├── validacao.py          # Checagem de imagem, limites de SP e mascaramento LGPD
│       ├── deduplicacao.py       # Deduplicação espacial (30m) e temporal (14 dias)
│       ├── geo.py                # Point-in-polygon com GeoJSON/Shapefiles do GeoSampa
│       ├── prioridade.py         # Matriz de prioridade (tipo + dados Infosiga)
│       ├── pacote.py             # Compilação e exportação de CSV e PDF por subprefeitura
│       └── main.py               # Orquestrador do lote, laço de execução e sumário
├── data/                         # Arquivos estáticos locais (polígonos e dados temporários)
│   ├── geosampa_subprefeituras.geojson
│   └── infosiga_sinistros_mock.csv
├── assets/                       # Evidências visuais, prints e saídas de exemplo
├── logs/
│   └── execucao_amostra.jsonl    # Logs estruturados JSON sanitizados (sem dados pessoais)
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Fixtures, mocks de APIs e geradores de dados
│   ├── test_validacao.py
│   ├── test_deduplicacao.py
│   ├── test_prioridade.py
│   └── test_pipeline_integracao.py
├── Dockerfile                    # Container para execução agendada e sob demanda
├── docker-compose.yml            # Orquestração local do container e mocks
├── pyproject.toml / requirements.txt
└── README.md                     # Documentação oficial, arquitetura e links
3. Especificação Detalhada dos Módulos
config.py
Gerenciamento de variáveis de ambiente:
API_BASE_URL
(URL da API principal do Passo Seguro)
.
VISION_API_URL
(Endpoint do detector YOLO/ONNX)
.
GEOSAMPA_DATA_PATH
(Caminho para polígonos GeoJSON das subprefeituras).
INFOSIGA_CSV_PATH
(Caminho para a base de atropelamentos do Infosiga)
.
INTERVALO_EXECUCAO_MINUTOS
(Padrão: 30)
.
LOG_LEVEL
(Padrão:
INFO
).
cliente_api.py
(Resiliência & I/O)
Consumo:
GET /relatos?status=novo&page={page}
paginação automatizada até esgotar o lote
.
Inferência de Visão (se pendente):
POST /deteccoes
enviando a imagem para validação de classes (
buraco
,
piso_danificado
,
obstaculo
,
veiculo_na_calcada
)
.
Atualização:
PATCH /relatos/{id}
atualizando para
encaminhado
,
revisao_humana
ou
rejeitado
.
Resiliência (Slide de Exceções & Resiliência):
Implementar
exponential backoff
com biblioteca
tenacity
ou
urllib3.util.retry
(3 tentativas com espera progressiva: 1s, 2s, 4s)
.
Tratar falha total da API de visão sem interromper o script (marca item como pendente/erro e loga adequadamente)
.
validacao.py
(LGPD & Integridade)
Validação de Imagem:
Valida cabeçalho da imagem com Pillow (
PIL.Image.open
), verificando se o buffer não está corrompido e possui dimensões mínimas válidas.
Validação Territorial Prévia:
Checa se a latitude e a longitude caem dentro da
Bounding Box
aproximada do município de São Paulo (
lat: -24.0 a -23.3, lon: -46.9 a -46.3
).
Mascaramento e LGPD:
Regex para ofuscação de CPF:
\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b
➔
***.***.***-**
.
Regex para ofuscação de Telefone:
\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9?\d{4})[-.\s]?\d{4}\b
➔
(**) *****-****
.
Anonimização de autor em logs e relatórios.
deduplicacao.py
(Espacial & Temporal)
Algoritmo de Haversine em Python nativo ou
geopy
para cálculo de distância métrica geodésica.
Critério: Caso já exista outro relato do
mesmo tipo de problema
registrado a
menos de 30 metros
em uma janela de até
14 dias anteriores
, o relato corrente é marcado como
duplicado
e seu status muda para
rejeitado
com o motivo
"duplicidade_geografica"
.
geo.py
(Enriquecimento Territorial)
Utilização de
shapely
e
geopandas
(ou
shapely.geometry.Point
com GeoJSON carregado).
Realiza o teste geométrico
point-in-polygon
contra os limites das 32 Subprefeituras e Distritos de SP (dados GeoSampa)
.
Retorna:
subprefeitura
(ex.: "Sé", "Pinheiros", "Mooca") e
distrito
. Se estiver fora do perímetro da capital, rejeita por inconsistência de localização
.
prioridade.py
(Regras de Decisão)
Gateway 1 (Confiança da Visão):
Se
confiança < 0.60
: desvia para
revisao_humana
.
Gateway 2 (Cálculo de Severidade e Histórico de Acidentes):
Cruzamento da coordenada com o mapa de calor/raio de 150m de atropelamentos do Infosiga (usando o CSV filtrado à mão do Infosiga SP)
.
Severidade da classe:
buraco
ou
veiculo_na_calcada
recebem peso base maior
.
Resultado:
ALTA
(área com sinistro fatal/grave recente ou obstáculo crítico em vias arteriais) ou
NORMAL
/
BAIXA
.
pacote.py
(Despacho SP156)
Agrupa todos os relatos validados e classificados na execução por
subprefeitura
.
Gera em
dist/pacotes/YYYY-MM-DD/
:
pacote_SP156_{subprefeitura}_{data}.csv
: Tabela sumarizada com IDs anonimizados, tipo, latitude/longitude, endereço aproximado e prioridade.
relatorio_SP156_{subprefeitura}_{data}.pdf
: Relatório visual para abertura de chamado municipal (utilizando
reportlab
ou
fpdf2
).
main.py
(Orquestração do Lote e Logs)
Laço iterativo com isolamento de falha (
try/except
por relato individual) — a falha em 1 relato nunca derruba a execução do lote
.
Auditoria e Logs Estruturados (
logs/
):
Padrão JSON Lines (
.jsonl
) na saída padrão (
stdout
) e em arquivo
logs/triagem_{data}.log
.
Formato:
JSON
{
"timestamp"
:
"2026-11-07T14:30:00Z"
,
"item_hash"
:
"a1b2c3d4..."
,
"etapa"
:
"geo_enrichment"
,
"status"
:
"sucesso"
,
"mensagem"
:
"Subprefeitura Sé identificada"
}
Regra LGPD:
Nunca registrar foto binária, textos livres descritivos ou coordenadas exatas no log (usar hash/ID mascarado)
.
Resumo Final de Lote:
Exibe e registra métricas:
processados
,
encaminhados
,
duplicados
,
rejeitados
,
erros
.
4. Estratégia de Testes Automatizados (
tests/
)
Construir cenários com
pytest
e
responses
/
unittest.mock
cobrindo
:
Cenário de Sucesso:
Lote padrão com relatos íntegros processados e marcados como
encaminhado
.
Cenário de Decisão (Gateways):
Relato em zona de atropelamento classificado como prioridade alta vs. relato de trinca superficial como prioridade baixa
.
Cenário de Resiliência/Falha de Serviço:
API de visão retornando HTTP 503 com acionamento do retry e degradação suave
.
Cenário de Dado Inválido:
Foto corrompida / payload sem coordenadas sendo rejeitado com log de auditoria correto
.
Cenário de Deduplicação:
Dois relatos a 15m de distância no intervalo de 3 dias gerando 1 aprovação e 1 descarte por duplicidade
.
5. Roteiro Operacional para Execução e Vídeo (Até 3 Minutos)
Garantir que a pipeline forneça flags CLI e mocks prontos para a gravação da demonstração
:
Comando sob demanda:
python -m src.triagem.main --executar-uma-vez --mock-data tests/fixtures/lote_demo.json
.
Roteiro de Gravação:
0:00 - 0:30
: Problema dos chamados de calçadas em SP e papel do robô na triagem ágil
.
0:30 - 1:30
: Execução ao vivo do lote de 10 casos (demonstrando 1 duplicado descartado, 1 foto inválida rejeitada e 1 caso com alta prioridade)
.
1:30 - 2:15
: Exibição do terminal com logs JSON sanitizados, sumário do lote e abertura dos arquivos CSV/PDF gerados na pasta de subprefeitura
.
2:15 - 2:45
: Simulação de resiliência: derrubar o mock da API de visão e mostrar as 3 tentativas no log sem quebrar a execução geral
.
2:45 - 3:00
: Conferência do PWA/API mostrando o status atualizado para "encaminhado"
.
Qual parte da implementação você quer detalhar primeiro: o script da esteira de processamento (
src/triagem/main.py
), a lógica de enriquecimento geográfico/GeoSampa ou as fixtures de teste para rodar contra os mocks?

==================================================

## Pergunta do Usuário:

Você disse
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo faze…
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo fazer tudo pois as outras partes ainda estao sendo feitas, mas quero começar e fazer o prototipo ja, preparar a pipeline e todas as coisas, a ideia esta dentro deste texte que ja havia te mandado, agora preciso que voce melhore, e entregue o contexto de tudo que deve ser feito, para que eu repasse para o antigravity
6 · Automação (Robotic Process Automation)
A triagem é a última peça técnica a ficar pronta porque depende de três outras, então o desenho e o código contra mocks começam antes. Responsável: Guilherme. Repositório: -rpa. Nota: desenvolvimento 5, documentação 2, vídeo 2, integração 1. Até a Ouro sair (13/11), a regra de prioridade usa um CSV do Infosiga filtrado à mão.
Antes: GET /relatos e atualização de status (parte 1), /deteccoes (parte 4) e a lista de atropelamentos exportada da Ouro (parte 3). Depois: o status "encaminhado" aparece no PWA (parte 1); o pacote por subprefeitura entra no pitch (parte 8).
Passo a passo
09–10/11 · Desenho. BPMN no bpmn.io ou Camunda Modeler com início, entradas, cada etapa, os dois gateways de decisão (classe com confiança baixa; prioridade), o laço sobre os relatos, os caminhos de exceção e as saídas. Salvar em docs/.
11/11 · Estrutura do código em src/triagem/:
cliente_api.py: busca relatos novos página a página e atualiza status
validacao.py: foto abre, coordenada dentro do município, mascara telefone e CPF por regex
deduplicacao.py: mesmo tipo a menos de 30 m em 14 dias (consulta PostGIS ou fórmula de haversine)
geo.py: subprefeitura e distrito por ponto no polígono, com os limites do GeoSampa salvos no repositório
prioridade.py: a regra de decisão da aba principal
pacote.py: CSV e PDF diários por subprefeitura
main.py: o laço e o resumo final
11/11 · Agendamento. Container triagem com execução a cada 30 minutos, e um comando para rodar uma vez sob demanda (útil no vídeo).
12/11 · Exceções. Três tentativas com espera crescente quando uma API não responde; try/except por item para um relato com problema não derrubar o lote; resumo final com processados, encaminhados, duplicados, rejeitados e erros.
13/11 · Logs. Uma linha JSON por item em logs/ e na saída padrão: data-hora, id com hash, etapa, resultado, mensagem de erro. Nunca foto, texto livre ou coordenada exata. Versionar uma amostra limpa.
13–14/11 · Testes com pytest, com a API simulada:
sucesso: lote normal encaminhado
decisão: um caso de prioridade alta e um de baixa
falha: serviço de visão fora (retentativa e registro) e foto corrompida (rejeitado com motivo)
14/11 · Integração. Rodar contra o ambiente publicado e printar o relato mudando para "encaminhado" no PWA.
15–16/11 · PDF e vídeo.
Roteiro do vídeo (até 3 minutos)
0:00 O problema e o papel da automação.
0:30 Rodar com um lote de 10 relatos preparado: 1 duplicado, 1 foto inválida, 1 de prioridade alta.
1:30 Mostrar os logs, o resumo e o pacote gerado.
2:15 Derrubar o serviço de visão e mostrar a retentativa e o registro da falha.
2:45 O app com os status atualizados.
Entrega
Repositório com src/, docs/, assets/, logs/, tests/ e README (descrição, integrantes, arquitetura, instruções, links)
PDF: integrantes; CitizenTech e problema; objetivo e benefício ao cidadão; processo e fluxo; tecnologias e justificativa; regras de negócio; exceções; logs; integração com o MVP; testes; segurança e LGPD; links do repositório e do vídeo
Vídeo de até 3 minutos
Envio na tarefa do Teams com tudo dentro do PDF

--------------------------------------------------

## Pergunta do Usuário:

Você disse
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo faze…
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo fazer tudo pois as outras partes ainda estao sendo feitas, mas quero começar e fazer o prototipo ja, preparar a pipeline e todas as coisas, a ideia esta dentro deste texte que ja havia te mandado, agora preciso que voce melhore, e entregue o contexto de tudo que deve ser feito, para que eu repasse para o antigravity
6 · Automação (Robotic Process Automation)
A triagem é a última peça técnica a ficar pronta porque depende de três outras, então o desenho e o código contra mocks começam antes. Responsável: Guilherme. Repositório: -rpa. Nota: desenvolvimento 5, documentação 2, vídeo 2, integração 1. Até a Ouro sair (13/11), a regra de prioridade usa um CSV do Infosiga filtrado à mão.
Antes: GET /relatos e atualização de status (parte 1), /deteccoes (parte 4) e a lista de atropelamentos exportada da Ouro (parte 3). Depois: o status "encaminhado" aparece no PWA (parte 1); o pacote por subprefeitura entra no pitch (parte 8).
Passo a passo
09–10/11 · Desenho. BPMN no bpmn.io ou Camunda Modeler com início, entradas, cada etapa, os dois gateways de decisão (classe com confiança baixa; prioridade), o laço sobre os relatos, os caminhos de exceção e as saídas. Salvar em docs/.
11/11 · Estrutura do código em src/triagem/:
cliente_api.py: busca relatos novos página a página e atualiza status
validacao.py: foto abre, coordenada dentro do município, mascara telefone e CPF por regex
deduplicacao.py: mesmo tipo a menos de 30 m em 14 dias (consulta PostGIS ou fórmula de haversine)
geo.py: subprefeitura e distrito por ponto no polígono, com os limites do GeoSampa salvos no repositório
prioridade.py: a regra de decisão da aba principal
pacote.py: CSV e PDF diários por subprefeitura
main.py: o laço e o resumo final
11/11 · Agendamento. Container triagem com execução a cada 30 minutos, e um comando para rodar uma vez sob demanda (útil no vídeo).
12/11 · Exceções. Três tentativas com espera crescente quando uma API não responde; try/except por item para um relato com problema não derrubar o lote; resumo final com processados, encaminhados, duplicados, rejeitados e erros.
13/11 · Logs. Uma linha JSON por item em logs/ e na saída padrão: data-hora, id com hash, etapa, resultado, mensagem de erro. Nunca foto, texto livre ou coordenada exata. Versionar uma amostra limpa.
13–14/11 · Testes com pytest, com a API simulada:
sucesso: lote normal encaminhado
decisão: um caso de prioridade alta e um de baixa
falha: serviço de visão fora (retentativa e registro) e foto corrompida (rejeitado com motivo)
14/11 · Integração. Rodar contra o ambiente publicado e printar o relato mudando para "encaminhado" no PWA.
15–16/11 · PDF e vídeo.
Roteiro do vídeo (até 3 minutos)
0:00 O problema e o papel da automação.
0:30 Rodar com um lote de 10 relatos preparado: 1 duplicado, 1 foto inválida, 1 de prioridade alta.
1:30 Mostrar os logs, o resumo e o pacote gerado.
2:15 Derrubar o serviço de visão e mostrar a retentativa e o registro da falha.
2:45 O app com os status atualizados.
Entrega
Repositório com src/, docs/, assets/, logs/, tests/ e README (descrição, integrantes, arquitetura, instruções, links)
PDF: integrantes; CitizenTech e problema; objetivo e benefício ao cidadão; processo e fluxo; tecnologias e justificativa; regras de negócio; exceções; logs; integração com o MVP; testes; segurança e LGPD; links do repositório e do vídeo
Vídeo de até 3 minutos
Envio na tarefa do Teams com tudo dentro do PDF

--------------------------------------------------

## Pergunta do Usuário:

Você disse
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo faze…
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo fazer tudo pois as outras partes ainda estao sendo feitas, mas quero começar e fazer o prototipo ja, preparar a pipeline e todas as coisas, a ideia esta dentro deste texte que ja havia te mandado, agora preciso que voce melhore, e entregue o contexto de tudo que deve ser feito, para que eu repasse para o antigravity
6 · Automação (Robotic Process Automation)
A triagem é a última peça técnica a ficar pronta porque depende de três outras, então o desenho e o código contra mocks começam antes. Responsável: Guilherme. Repositório: -rpa. Nota: desenvolvimento 5, documentação 2, vídeo 2, integração 1. Até a Ouro sair (13/11), a regra de prioridade usa um CSV do Infosiga filtrado à mão.
Antes: GET /relatos e atualização de status (parte 1), /deteccoes (parte 4) e a lista de atropelamentos exportada da Ouro (parte 3). Depois: o status "encaminhado" aparece no PWA (parte 1); o pacote por subprefeitura entra no pitch (parte 8).
Passo a passo
09–10/11 · Desenho. BPMN no bpmn.io ou Camunda Modeler com início, entradas, cada etapa, os dois gateways de decisão (classe com confiança baixa; prioridade), o laço sobre os relatos, os caminhos de exceção e as saídas. Salvar em docs/.
11/11 · Estrutura do código em src/triagem/:
cliente_api.py: busca relatos novos página a página e atualiza status
validacao.py: foto abre, coordenada dentro do município, mascara telefone e CPF por regex
deduplicacao.py: mesmo tipo a menos de 30 m em 14 dias (consulta PostGIS ou fórmula de haversine)
geo.py: subprefeitura e distrito por ponto no polígono, com os limites do GeoSampa salvos no repositório
prioridade.py: a regra de decisão da aba principal
pacote.py: CSV e PDF diários por subprefeitura
main.py: o laço e o resumo final
11/11 · Agendamento. Container triagem com execução a cada 30 minutos, e um comando para rodar uma vez sob demanda (útil no vídeo).
12/11 · Exceções. Três tentativas com espera crescente quando uma API não responde; try/except por item para um relato com problema não derrubar o lote; resumo final com processados, encaminhados, duplicados, rejeitados e erros.
13/11 · Logs. Uma linha JSON por item em logs/ e na saída padrão: data-hora, id com hash, etapa, resultado, mensagem de erro. Nunca foto, texto livre ou coordenada exata. Versionar uma amostra limpa.
13–14/11 · Testes com pytest, com a API simulada:
sucesso: lote normal encaminhado
decisão: um caso de prioridade alta e um de baixa
falha: serviço de visão fora (retentativa e registro) e foto corrompida (rejeitado com motivo)
14/11 · Integração. Rodar contra o ambiente publicado e printar o relato mudando para "encaminhado" no PWA.
15–16/11 · PDF e vídeo.
Roteiro do vídeo (até 3 minutos)
0:00 O problema e o papel da automação.
0:30 Rodar com um lote de 10 relatos preparado: 1 duplicado, 1 foto inválida, 1 de prioridade alta.
1:30 Mostrar os logs, o resumo e o pacote gerado.
2:15 Derrubar o serviço de visão e mostrar a retentativa e o registro da falha.
2:45 O app com os status atualizados.
Entrega
Repositório com src/, docs/, assets/, logs/, tests/ e README (descrição, integrantes, arquitetura, instruções, links)
PDF: integrantes; CitizenTech e problema; objetivo e benefício ao cidadão; processo e fluxo; tecnologias e justificativa; regras de negócio; exceções; logs; integração com o MVP; testes; segurança e LGPD; links do repositório e do vídeo
Vídeo de até 3 minutos
Envio na tarefa do Teams com tudo dentro do PDF

--------------------------------------------------

## Pergunta do Usuário:

Você disse
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo faze…
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo fazer tudo pois as outras partes ainda estao sendo feitas, mas quero começar e fazer o prototipo ja, preparar a pipeline e todas as coisas, a ideia esta dentro deste texte que ja havia te mandado, agora preciso que voce melhore, e entregue o contexto de tudo que deve ser feito, para que eu repasse para o antigravity
6 · Automação (Robotic Process Automation)
A triagem é a última peça técnica a ficar pronta porque depende de três outras, então o desenho e o código contra mocks começam antes. Responsável: Guilherme. Repositório: -rpa. Nota: desenvolvimento 5, documentação 2, vídeo 2, integração 1. Até a Ouro sair (13/11), a regra de prioridade usa um CSV do Infosiga filtrado à mão.
Antes: GET /relatos e atualização de status (parte 1), /deteccoes (parte 4) e a lista de atropelamentos exportada da Ouro (parte 3). Depois: o status "encaminhado" aparece no PWA (parte 1); o pacote por subprefeitura entra no pitch (parte 8).
Passo a passo
09–10/11 · Desenho. BPMN no bpmn.io ou Camunda Modeler com início, entradas, cada etapa, os dois gateways de decisão (classe com confiança baixa; prioridade), o laço sobre os relatos, os caminhos de exceção e as saídas. Salvar em docs/.
11/11 · Estrutura do código em src/triagem/:
cliente_api.py: busca relatos novos página a página e atualiza status
validacao.py: foto abre, coordenada dentro do município, mascara telefone e CPF por regex
deduplicacao.py: mesmo tipo a menos de 30 m em 14 dias (consulta PostGIS ou fórmula de haversine)
geo.py: subprefeitura e distrito por ponto no polígono, com os limites do GeoSampa salvos no repositório
prioridade.py: a regra de decisão da aba principal
pacote.py: CSV e PDF diários por subprefeitura
main.py: o laço e o resumo final
11/11 · Agendamento. Container triagem com execução a cada 30 minutos, e um comando para rodar uma vez sob demanda (útil no vídeo).
12/11 · Exceções. Três tentativas com espera crescente quando uma API não responde; try/except por item para um relato com problema não derrubar o lote; resumo final com processados, encaminhados, duplicados, rejeitados e erros.
13/11 · Logs. Uma linha JSON por item em logs/ e na saída padrão: data-hora, id com hash, etapa, resultado, mensagem de erro. Nunca foto, texto livre ou coordenada exata. Versionar uma amostra limpa.
13–14/11 · Testes com pytest, com a API simulada:
sucesso: lote normal encaminhado
decisão: um caso de prioridade alta e um de baixa
falha: serviço de visão fora (retentativa e registro) e foto corrompida (rejeitado com motivo)
14/11 · Integração. Rodar contra o ambiente publicado e printar o relato mudando para "encaminhado" no PWA.
15–16/11 · PDF e vídeo.
Roteiro do vídeo (até 3 minutos)
0:00 O problema e o papel da automação.
0:30 Rodar com um lote de 10 relatos preparado: 1 duplicado, 1 foto inválida, 1 de prioridade alta.
1:30 Mostrar os logs, o resumo e o pacote gerado.
2:15 Derrubar o serviço de visão e mostrar a retentativa e o registro da falha.
2:45 O app com os status atualizados.
Entrega
Repositório com src/, docs/, assets/, logs/, tests/ e README (descrição, integrantes, arquitetura, instruções, links)
PDF: integrantes; CitizenTech e problema; objetivo e benefício ao cidadão; processo e fluxo; tecnologias e justificativa; regras de negócio; exceções; logs; integração com o MVP; testes; segurança e LGPD; links do repositório e do vídeo
Vídeo de até 3 minutos
Envio na tarefa do Teams com tudo dentro do PDF

--------------------------------------------------

## Pergunta do Usuário:

Você disse
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo faze…
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo fazer tudo pois as outras partes ainda estao sendo feitas, mas quero começar e fazer o prototipo ja, preparar a pipeline e todas as coisas, a ideia esta dentro deste texte que ja havia te mandado, agora preciso que voce melhore, e entregue o contexto de tudo que deve ser feito, para que eu repasse para o antigravity
6 · Automação (Robotic Process Automation)
A triagem é a última peça técnica a ficar pronta porque depende de três outras, então o desenho e o código contra mocks começam antes. Responsável: Guilherme. Repositório: -rpa. Nota: desenvolvimento 5, documentação 2, vídeo 2, integração 1. Até a Ouro sair (13/11), a regra de prioridade usa um CSV do Infosiga filtrado à mão.
Antes: GET /relatos e atualização de status (parte 1), /deteccoes (parte 4) e a lista de atropelamentos exportada da Ouro (parte 3). Depois: o status "encaminhado" aparece no PWA (parte 1); o pacote por subprefeitura entra no pitch (parte 8).
Passo a passo
09–10/11 · Desenho. BPMN no bpmn.io ou Camunda Modeler com início, entradas, cada etapa, os dois gateways de decisão (classe com confiança baixa; prioridade), o laço sobre os relatos, os caminhos de exceção e as saídas. Salvar em docs/.
11/11 · Estrutura do código em src/triagem/:
cliente_api.py: busca relatos novos página a página e atualiza status
validacao.py: foto abre, coordenada dentro do município, mascara telefone e CPF por regex
deduplicacao.py: mesmo tipo a menos de 30 m em 14 dias (consulta PostGIS ou fórmula de haversine)
geo.py: subprefeitura e distrito por ponto no polígono, com os limites do GeoSampa salvos no repositório
prioridade.py: a regra de decisão da aba principal
pacote.py: CSV e PDF diários por subprefeitura
main.py: o laço e o resumo final
11/11 · Agendamento. Container triagem com execução a cada 30 minutos, e um comando para rodar uma vez sob demanda (útil no vídeo).
12/11 · Exceções. Três tentativas com espera crescente quando uma API não responde; try/except por item para um relato com problema não derrubar o lote; resumo final com processados, encaminhados, duplicados, rejeitados e erros.
13/11 · Logs. Uma linha JSON por item em logs/ e na saída padrão: data-hora, id com hash, etapa, resultado, mensagem de erro. Nunca foto, texto livre ou coordenada exata. Versionar uma amostra limpa.
13–14/11 · Testes com pytest, com a API simulada:
sucesso: lote normal encaminhado
decisão: um caso de prioridade alta e um de baixa
falha: serviço de visão fora (retentativa e registro) e foto corrompida (rejeitado com motivo)
14/11 · Integração. Rodar contra o ambiente publicado e printar o relato mudando para "encaminhado" no PWA.
15–16/11 · PDF e vídeo.
Roteiro do vídeo (até 3 minutos)
0:00 O problema e o papel da automação.
0:30 Rodar com um lote de 10 relatos preparado: 1 duplicado, 1 foto inválida, 1 de prioridade alta.
1:30 Mostrar os logs, o resumo e o pacote gerado.
2:15 Derrubar o serviço de visão e mostrar a retentativa e o registro da falha.
2:45 O app com os status atualizados.
Entrega
Repositório com src/, docs/, assets/, logs/, tests/ e README (descrição, integrantes, arquitetura, instruções, links)
PDF: integrantes; CitizenTech e problema; objetivo e benefício ao cidadão; processo e fluxo; tecnologias e justificativa; regras de negócio; exceções; logs; integração com o MVP; testes; segurança e LGPD; links do repositório e do vídeo
Vídeo de até 3 minutos
Envio na tarefa do Teams com tudo dentro do PDF

--------------------------------------------------

## Pergunta do Usuário:

Você disse
Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo faze…

--------------------------------------------------

## Pergunta do Usuário:

Para começar este projeto farei apenas algumas partes, começando pela automação, eu nao consigo fazer tudo pois as outras partes ainda estao sendo feitas, mas quero começar e fazer o prototipo ja, preparar a pipeline e todas as coisas, a ideia esta dentro deste texte que ja havia te mandado, agora preciso que voce melhore, e entregue o contexto de tudo que deve ser feito, para que eu repasse para o antigravity

--------------------------------------------------

## Pergunta do Usuário:



--------------------------------------------------

## Pergunta do Usuário:

6 · Automação (Robotic Process Automation)

--------------------------------------------------

## Pergunta do Usuário:

A triagem é a última peça técnica a ficar pronta porque depende de três outras, então o desenho e o código contra mocks começam antes. Responsável: Guilherme. Repositório: -rpa. Nota: desenvolvimento 5, documentação 2, vídeo 2, integração 1. Até a Ouro sair (13/11), a regra de prioridade usa um CSV do Infosiga filtrado à mão.

--------------------------------------------------

## Pergunta do Usuário:

Antes: GET /relatos e atualização de status (parte 1), /deteccoes (parte 4) e a lista de atropelamentos exportada da Ouro (parte 3). Depois: o status "encaminhado" aparece no PWA (parte 1); o pacote por subprefeitura entra no pitch (parte 8).

--------------------------------------------------

## Pergunta do Usuário:

Passo a passo

--------------------------------------------------

## Pergunta do Usuário:

Roteiro do vídeo (até 3 minutos)

--------------------------------------------------

## Pergunta do Usuário:

Entrega

--------------------------------------------------
