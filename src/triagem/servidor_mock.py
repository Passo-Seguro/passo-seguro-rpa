import argparse
import base64
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, FileResponse
from starlette.routing import Route

from src.triagem.config import settings

MOCK_FILE = Path("data/relatos_mock.json")
FOTOS_DIR = Path("data/amostras_fotos")


def carregar_relatos() -> List[Dict[str, Any]]:
    if not MOCK_FILE.exists():
        origem = Path("tests/fixtures/lote_demo.json")
        if origem.exists():
            MOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(origem, "r", encoding="utf-8") as f:
                dados = json.load(f)
            with open(MOCK_FILE, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            return dados
        return []
    with open(MOCK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_relatos(relatos: List[Dict[str, Any]]):
    MOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(relatos, f, ensure_ascii=False, indent=2)


# --- ROTAS DA API ---

async def saude(request: Request) -> JSONResponse:
    """Verificação de integridade da API mock."""
    return JSONResponse({
        "status": "ok",
        "servico": "passo-seguro-mock-server",
        "modo_fake": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


async def listar_relatos(request: Request) -> JSONResponse:
    """GET /relatos e /api/relatos: Lista relatos com suporte a filtro por status e paginação."""
    status_filtro = request.query_params.get("status")
    pagina = int(request.query_params.get("pagina", 1))
    tamanho = int(request.query_params.get("tamanho", 50))

    relatos = carregar_relatos()
    if status_filtro:
        relatos = [r for r in relatos if r.get("status") == status_filtro]

    inicio = (pagina - 1) * tamanho
    fim = inicio + tamanho
    itens_pagina = relatos[inicio:fim]

    return JSONResponse({
        "itens": itens_pagina,
        "paginacao": {
            "pagina": pagina,
            "tamanho": tamanho,
            "total_itens": len(relatos),
            "total_paginas": (len(relatos) + tamanho - 1) // tamanho if relatos else 1,
            "tem_proxima": fim < len(relatos)
        }
    })


async def criar_relato(request: Request) -> JSONResponse:
    """POST /relatos e /api/relatos: Recebe novo relato do cidadão (multipart ou JSON)."""
    novo_id = str(uuid.uuid4())
    content_type = request.headers.get("content-type", "")

    lat, lon, descricao, categoria = -23.5504, -46.6332, "", "buraco"
    foto_nome = f"{novo_id}.jpg"
    foto_caminho = FOTOS_DIR / foto_nome

    if "multipart/form-data" in content_type:
        form = await request.form()
        lat = float(form.get("lat", form.get("latitude", lat)))
        lon = float(form.get("lon", form.get("longitude", lon)))
        descricao = str(form.get("descricao", ""))
        categoria = str(form.get("categoria", form.get("tipo", "buraco")))

        arquivo_foto = form.get("foto") or form.get("imagem")
        if arquivo_foto and hasattr(arquivo_foto, "read"):
            FOTOS_DIR.mkdir(parents=True, exist_ok=True)
            conteudo = await arquivo_foto.read()
            foto_caminho.write_bytes(conteudo)
    else:
        dados = await request.json()
        lat = float(dados.get("lat", dados.get("latitude", lat)))
        lon = float(dados.get("lon", dados.get("longitude", lon)))
        descricao = str(dados.get("descricao", ""))
        categoria = str(dados.get("categoria", dados.get("tipo", "buraco")))

    novo_relato = {
        "id": novo_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lat": lat,
        "lon": lon,
        "latitude": lat,
        "longitude": lon,
        "tipo": categoria,
        "categoria": categoria,
        "descricao": descricao,
        "status": "novo",
        "foto_url": f"http://localhost:8000/api/fotos/relatos/{foto_nome}",
        "subprefeitura": None,
        "prioridade": None
    }

    relatos = carregar_relatos()
    relatos.insert(0, novo_relato)
    salvar_relatos(relatos)

    return JSONResponse(novo_relato, status_code=201)


async def atualizar_relato(request: Request) -> JSONResponse:
    """PATCH /relatos/{id} e /api/relatos/{id}: Atualiza status e prioridade."""
    id_relato = request.path_params.get("id")
    dados = await request.json()

    relatos = carregar_relatos()
    relato_encontrado = None

    for r in relatos:
        if str(r.get("id")) == str(id_relato):
            r.update(dados)
            relato_encontrado = r
            break

    if not relato_encontrado:
        return JSONResponse({"erro": "relato_nao_encontrado"}, status_code=404)

    salvar_relatos(relatos)
    return JSONResponse(relato_encontrado)


async def servir_foto(request: Request) -> Response:
    """GET /fotos/relatos/{nome} e /api/fotos/relatos/{nome}."""
    nome = request.path_params.get("nome")
    caminho = FOTOS_DIR / nome
    if caminho.exists():
        return FileResponse(str(caminho), media_type="image/jpeg")

    # Fallback para amostras se o arquivo exato não estiver presente
    amostras = list(FOTOS_DIR.glob("*.jpg"))
    if amostras:
        return FileResponse(str(amostras[0]), media_type="image/jpeg")

    return Response("Foto não encontrada", status_code=404)


async def mock_deteccoes_visao(request: Request) -> JSONResponse:
    """POST /deteccoes: Simula o microserviço de Visão Computacional (YOLO)."""
    form = await request.form()
    imagem = form.get("imagem")

    # Detecção inteligente simulada com classes do contrato oficial
    classe = "buraco"
    confianca = 0.85
    caixa = {"x": 0.22, "y": 0.38, "largura": 0.38, "altura": 0.26}

    if imagem and hasattr(imagem, "filename"):
        nome_arquivo = imagem.filename.lower()
        if "piso" in nome_arquivo or "rachad" in nome_arquivo:
            classe = "piso_danificado"
            confianca = 0.82
        elif "obstaculo" in nome_arquivo or "entulho" in nome_arquivo:
            classe = "obstaculo"
            confianca = 0.79
        elif "veiculo" in nome_arquivo or "carro" in nome_arquivo:
            classe = "veiculo_na_calcada"
            confianca = 0.94
        elif "sem_defeito" in nome_arquivo:
            return JSONResponse([])

    return JSONResponse([
        {
            "classe": classe,
            "confianca": confianca,
            "caixa": caixa
        }
    ])


async def mock_assistente_genai(request: Request) -> JSONResponse:
    """POST /assistente: Simula o microserviço de IA Generativa (GenAI)."""
    dados = await request.json()
    pergunta = str(dados.get("pergunta", "")).strip().lower()

    if "buraco" in pergunta:
        return JSONResponse({
            "resposta": (
                "Para solicitar o conserto de um buraco na calçada, você deve registrar um chamado no portal "
                "SP156 da Prefeitura de São Paulo na categoria 'Calçadas - Vistoria e Reparo'. A Subprefeitura "
                "local notificará o responsável ou realizará o reparo se for de responsabilidade municipal."
            ),
            "fontes": [
                {"titulo": "Portal SP156 - Solicitação de Vistoria de Calçada", "url": "https://sp156.prefeitura.sp.gov.br/"},
                {"titulo": "Lei Municipal nº 15.442/2011 (Lei das Calçadas)", "url": "https://leismunicipais.com.br/a/sp/sao-paulo/lei-ordinaria/2011/1544/15442"}
            ],
            "confianca": 0.96,
            "recusou": False
        })
    elif "responsável" in pergunta or "responsavel" in pergunta or "casa" in pergunta or "prédio" in pergunta:
        return JSONResponse({
            "resposta": (
                "Segundo a Lei Municipal nº 15.442/2011, a construção, conservação e manutenção da calçada "
                "é de responsabilidade do proprietário ou morador do imóvel frontal. A Prefeitura é responsável "
                "apenas pelas calçadas em frente a prédios públicos municipais, praças e parques."
            ),
            "fontes": [
                {"titulo": "Cartilha de Calçadas de São Paulo - SEL/SMSUB", "url": "https://capital.sp.gov.br/web/urbanismo/calcadas"},
                {"titulo": "Decreto nº 58.845/2019 - Padrões de Calçadas SP", "url": "https://legislacao.prefeitura.sp.gov.br/"}
            ],
            "confianca": 0.98,
            "recusou": False
        })
    elif "vaso" in pergunta or "bloqueando" in pergunta or "obstru" in pergunta:
        return JSONResponse({
            "resposta": (
                "Nenhum objeto pode impedir a circulação de pedestres na faixa livre da calçada (mínimo de 1,20 m). "
                "Vasos, floreiras ou entulhos bloqueando a passagem violam o Código de Posturas Municipais. "
                "Você pode solicitar fiscalização da Subprefeitura pelo canal SP156."
            ),
            "fontes": [
                {"titulo": "Manual de Desenho Urbano e Calçadas SP", "url": "https://capital.sp.gov.br/"},
                {"titulo": "SP156 - Desobstrução de Passeio Público", "url": "https://sp156.prefeitura.sp.gov.br/"}
            ],
            "confianca": 0.95,
            "recusou": False
        })
    elif "carro" in pergunta:
        # Orientação oficial: recusa perguntas sobre estacionamento irregular (encaminha p/ CET)
        return JSONResponse({
            "resposta": (
                "O Passo Seguro foca no estado físico e conservação das calçadas. Para denúncias de veículos estacionados "
                "na calçada, a autuação compete à Companhia de Engenharia de Tráfego (CET pelo telefone 156 ou app CET SP)."
            ),
            "fontes": [
                {"titulo": "CET SP - Fiscalização de Trânsito", "url": "https://www.cetsp.com.br/"}
            ],
            "confianca": 0.91,
            "recusou": True
        })
    else:
        return JSONResponse({
            "resposta": (
                "O Passo Seguro orienta sobre a zeladoria urbana e conservação das calçadas de São Paulo. "
                "Para mais detalhes ou para registrar esta ocorrência, consulte os serviços municipais no portal SP156."
            ),
            "fontes": [
                {"titulo": "Prefeitura de São Paulo - SP156", "url": "https://sp156.prefeitura.sp.gov.br/"}
            ],
            "confianca": 0.85,
            "recusou": False
        })


async def painel_prioridades(request: Request) -> JSONResponse:
    """GET /painel e /api/painel: Devolve prioridades e totais por subprefeitura."""
    relatos = carregar_relatos()
    resumo: Dict[str, Dict[str, Any]] = {}

    for r in relatos:
        sub = r.get("subprefeitura") or "Outras_Regioes"
        if sub not in resumo:
            resumo[sub] = {"subprefeitura": sub, "total_relatos": 0, "alta": 0, "media": 0, "baixa": 0}
        resumo[sub]["total_relatos"] += 1
        prio = (r.get("prioridade") or "NORMAL").upper()
        if prio == "ALTA":
            resumo[sub]["alta"] += 1
        elif prio in ["NORMAL", "MEDIA"]:
            resumo[sub]["media"] += 1
        else:
            resumo[sub]["baixa"] += 1

    return JSONResponse(list(resumo.values()))


# --- MONTAGEM DA APLICAÇÃO STARLETTE ---

rotas = [
    # Saúde
    Route("/saude", saude, methods=["GET"]),
    Route("/health", saude, methods=["GET"]),
    Route("/api/saude", saude, methods=["GET"]),
    # Relatos
    Route("/relatos", listar_relatos, methods=["GET"]),
    Route("/relatos", criar_relato, methods=["POST"]),
    Route("/relatos/{id:str}", atualizar_relato, methods=["PATCH"]),
    Route("/api/relatos", listar_relatos, methods=["GET"]),
    Route("/api/relatos", criar_relato, methods=["POST"]),
    Route("/api/relatos/{id:str}", atualizar_relato, methods=["PATCH"]),
    # Fotos
    Route("/fotos/relatos/{nome:str}", servir_foto, methods=["GET"]),
    Route("/api/fotos/relatos/{nome:str}", servir_foto, methods=["GET"]),
    # Microserviços
    Route("/deteccoes", mock_deteccoes_visao, methods=["POST"]),
    Route("/api/deteccoes", mock_deteccoes_visao, methods=["POST"]),
    Route("/assistente", mock_assistente_genai, methods=["POST"]),
    Route("/api/assistente", mock_assistente_genai, methods=["POST"]),
    # Painel
    Route("/painel", painel_prioridades, methods=["GET"]),
    Route("/api/painel", painel_prioridades, methods=["GET"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(debug=True, routes=rotas, middleware=middleware)


def main():
    parser = argparse.ArgumentParser(description="Servidor Mock Unificado do Passo Seguro")
    parser.add_argument("--porta", type=int, default=8000, help="Porta HTTP do servidor mock (padrão: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host de escuta (padrão: 127.0.0.1)")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(" 🚀 SERVIDOR MOCK UNIFICADO - PASSO SEGURO")
    print("=" * 70)
    print(f" • Endereço Base:   http://{args.host}:{args.porta}")
    print(f" • API Central:     http://{args.host}:{args.porta}/api/relatos")
    print(f" • Visão (YOLO):    http://{args.host}:{args.porta}/deteccoes")
    print(f" • GenAI Assistent: http://{args.host}:{args.porta}/assistente")
    print(f" • Painel/Dashboard:http://{args.host}:{args.porta}/api/painel")
    print(f" • Base Mockada:    {MOCK_FILE}")
    print("=" * 70 + "\n")

    uvicorn.run(app, host=args.host, port=args.porta, log_level="info")


if __name__ == "__main__":
    main()
