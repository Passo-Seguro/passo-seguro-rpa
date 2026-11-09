import csv
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

from src.triagem.config import settings
from src.triagem.deduplicacao import calcular_distancia_haversine

_INFOSIGA_CACHE: Optional[List[Dict[str, Any]]] = None


def carregar_base_infosiga(caminho_csv: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Carrega dados de acidentes e atropelamentos do Infosiga para memória com cache."""
    global _INFOSIGA_CACHE
    if _INFOSIGA_CACHE is not None:
        return _INFOSIGA_CACHE

    caminho = caminho_csv or settings.infosiga_csv_path
    if not Path(caminho).exists():
        alt = Path("data/infosiga_sinistros.csv") if "mock" in str(caminho) else Path("data/infosiga_sinistros_mock.csv")
        if alt.exists():
            caminho = alt
        else:
            _INFOSIGA_CACHE = []
            return _INFOSIGA_CACHE

    registros = []
    with open(caminho, mode="r", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            try:
                registros.append({
                    "id_sinistro": linha.get("id_sinistro"),
                    "data": linha.get("data"),
                    "tipo_vitima": linha.get("tipo_vitima"),
                    "gravidade": linha.get("gravidade", "GRAVE").upper(),
                    "logradouro": linha.get("logradouro"),
                    "latitude": float(linha["latitude"]),
                    "longitude": float(linha["longitude"]),
                    "subprefeitura": linha.get("subprefeitura")
                })
            except (ValueError, KeyError):
                continue

    _INFOSIGA_CACHE = registros
    return _INFOSIGA_CACHE


def verificar_proximidade_infosiga(
    latitude: float,
    longitude: float,
    raio_maximo: float = settings.raio_infosiga_metros
) -> Optional[Dict[str, Any]]:
    """
    Retorna o sinistro mais próximo se estiver dentro do raio estipulado (padrão: 150m).
    """
    sinistros = carregar_base_infosiga()
    sinistro_mais_proximo = None
    menor_distancia = float("inf")

    for s in sinistros:
        dist = calcular_distancia_haversine(latitude, longitude, s["latitude"], s["longitude"])
        if dist <= raio_maximo and dist < menor_distancia:
            menor_distancia = dist
            sinistro_mais_proximo = {**s, "distancia_metros": round(dist, 1)}

    return sinistro_mais_proximo


def avaliar_prioridade_e_status(
    relato: Dict[str, Any],
    dados_visao: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, str]:
    """
    Executa os Gateways de Decisão da triagem:
    1. Gateway de Confiança Visual: se confiança < limiar, desvia para 'revisao_humana'.
    2. Gateway de Prioridade: cruza severidade da classe de avaria com base de atropelamentos do Infosiga.
    Retorna: (status_recomendado, prioridade, justificativa)
    """
    tipo = relato.get("tipo", "outro")
    confianca = 1.0

    if dados_visao:
        confianca = dados_visao.get("confianca", 1.0)
        tipo = dados_visao.get("classe", tipo)

    # Gateway 1: Confiança da visão computacional
    if confianca < settings.limiar_confianca_visao:
        return (
            "revisao_humana",
            "NORMAL",
            f"Baixa confiança na classificação visual ({confianca:.2f} < {settings.limiar_confianca_visao:.2f})."
        )

    # Gateway 2: Cruzamento de risco territorial (Infosiga)
    lat = relato.get("latitude")
    lon = relato.get("longitude")
    sinistro_proximo = None
    if lat is not None and lon is not None:
        sinistro_proximo = verificar_proximidade_infosiga(lat, lon)

    # Classes consideradas de risco crítico imediato para pedestres e cadeirantes
    classes_criticas = ["buraco", "veiculo_na_calcada"]

    if sinistro_proximo:
        dist = sinistro_proximo["distancia_metros"]
        grav = sinistro_proximo["gravidade"]
        id_sin = sinistro_proximo["id_sinistro"]
        justificativa = (
            f"Área crítica: histórico de sinistro de trânsito {grav} ({id_sin}) a {dist}m da ocorrência."
        )
        return "validado", "ALTA", justificativa

    if tipo in classes_criticas:
        return (
            "validado",
            "ALTA" if tipo == "buraco" else "NORMAL",
            f"Avaria de classe de risco elevado ({tipo}), sem histórico recente de sinistro na coordenada."
        )

    if tipo == "piso_danificado":
        return "validado", "NORMAL", "Desnível ou lajota solta com risco moderado de queda."

    return "validado", "BAIXA", f"Ocorrência de gravidade leve ({tipo})."
