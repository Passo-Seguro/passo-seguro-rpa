import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from shapely.geometry import Point, shape

from src.triagem.config import settings

_GEOJSON_CACHE: Optional[List[Dict[str, Any]]] = None


def carregar_poligonos_subprefeituras(caminho_geojson: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Carrega as features de polígonos das subprefeituras em memória com cache."""
    global _GEOJSON_CACHE
    if _GEOJSON_CACHE is not None:
        return _GEOJSON_CACHE

    caminho = caminho_geojson or settings.geosampa_data_path
    if not Path(caminho).exists():
        raise FileNotFoundError(f"Arquivo GeoJSON não encontrado em: {caminho}")

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    _GEOJSON_CACHE = [
        {
            "properties": feat.get("properties", {}),
            "geometry": shape(feat.get("geometry"))
        }
        for feat in dados.get("features", [])
    ]
    return _GEOJSON_CACHE


def identificar_territorio(latitude: float, longitude: float) -> Optional[Dict[str, str]]:
    """
    Realiza o teste de Point-in-Polygon contra as subprefeituras e distritos de São Paulo.
    Retorna dicionário com subprefeitura, distrito e sigla ou None se fora do município.
    """
    poligonos = carregar_poligonos_subprefeituras()
    # GeoJSON segue padrão (longitude, latitude)
    ponto = Point(longitude, latitude)

    for item in poligonos:
        if item["geometry"].contains(ponto):
            props = item["properties"]
            return {
                "subprefeitura": props.get("subprefeitura", "Não Identificada"),
                "distrito": props.get("distrito", "Não Identificado"),
                "sigla": props.get("sigla", "SP")
            }

    return None
