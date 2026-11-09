import math
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Any, Optional

from src.triagem.config import settings

EARTH_RADIUS_METERS = 6371000.0


def calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância geodésica em metros entre dois pontos geográficos utilizando a fórmula de Haversine.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_METERS * c


def parse_timestamp(ts_str: str) -> datetime:
    """Converte string ISO de timestamp em objeto datetime ciente de fuso (UTC)."""
    try:
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.fromisoformat(ts_str)
    except Exception:
        return datetime.now(timezone.utc)


def verificar_duplicidade(
    relato_atual: Dict[str, Any],
    historico_relatos: List[Dict[str, Any]]
) -> Tuple[bool, Optional[str]]:
    """
    Verifica se existe duplicidade geográfica e temporal para o relato atual.
    Critério: mesmo tipo de dano a menos de 30m de distância em um intervalo de até 14 dias.
    """
    lat_atual = relato_atual.get("latitude")
    lon_atual = relato_atual.get("longitude")
    tipo_atual = relato_atual.get("tipo")
    id_atual = relato_atual.get("id")

    if lat_atual is None or lon_atual is None or not tipo_atual:
        return False, None

    dt_atual = parse_timestamp(relato_atual.get("timestamp", datetime.now(timezone.utc).isoformat()))

    for anterior in historico_relatos:
        if anterior.get("id") == id_atual:
            continue

        # Só compara relatos do mesmo tipo e que não tenham sido descartados como erro/rejeitados
        if anterior.get("tipo") != tipo_atual:
            continue
        if anterior.get("status") in ["rejeitado"]:
            continue

        lat_ant = anterior.get("latitude")
        lon_ant = anterior.get("longitude")
        if lat_ant is None or lon_ant is None:
            continue

        # Checagem temporal
        dt_ant = parse_timestamp(anterior.get("timestamp", datetime.now(timezone.utc).isoformat()))
        diferenca_dias = abs((dt_atual - dt_ant).total_seconds()) / 86400.0

        if diferenca_dias <= settings.janela_deduplicacao_dias:
            distancia = calcular_distancia_haversine(lat_atual, lon_atual, lat_ant, lon_ant)
            if distancia <= settings.raio_deduplicacao_metros:
                return True, (
                    f"Duplicidade com relato '{anterior.get('id')}': "
                    f"distância de {distancia:.1f}m (< {settings.raio_deduplicacao_metros}m) "
                    f"em {diferenca_dias:.1f} dias."
                )

    return False, None
