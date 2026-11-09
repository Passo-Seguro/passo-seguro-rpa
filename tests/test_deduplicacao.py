from src.triagem.deduplicacao import (
    calcular_distancia_haversine,
    verificar_duplicidade
)


def test_calcular_distancia_haversine():
    # Coordenadas com ~100m de distância
    lat1, lon1 = -23.5505, -46.6333
    lat2, lon2 = -23.5514, -46.6333
    distancia = calcular_distancia_haversine(lat1, lon1, lat2, lon2)
    assert 95.0 <= distancia <= 105.0


def test_deduplicacao_relato_duplicado():
    historico = [
        {
            "id": "relato-antigo",
            "timestamp": "2026-11-05T10:00:00Z",
            "tipo": "buraco",
            "latitude": -23.55050,
            "longitude": -46.63330,
            "status": "validado"
        }
    ]

    relato_novo = {
        "id": "relato-novo",
        "timestamp": "2026-11-07T10:00:00Z",  # 2 dias depois
        "tipo": "buraco",
        "latitude": -23.55055,  # ~6 metros de distância
        "longitude": -46.63330,
        "status": "novo"
    }

    is_dup, motivo = verificar_duplicidade(relato_novo, historico)
    assert is_dup is True
    assert "Duplicidade" in motivo


def test_deduplicacao_distancia_maior_que_limiar():
    historico = [
        {
            "id": "relato-antigo",
            "timestamp": "2026-11-05T10:00:00Z",
            "tipo": "buraco",
            "latitude": -23.55050,
            "longitude": -46.63330,
            "status": "validado"
        }
    ]

    # Relato a 80 metros de distância (limiar é 30m)
    relato_longe = {
        "id": "relato-longe",
        "timestamp": "2026-11-07T10:00:00Z",
        "tipo": "buraco",
        "latitude": -23.55120,
        "longitude": -46.63330,
        "status": "novo"
    }

    is_dup, motivo = verificar_duplicidade(relato_longe, historico)
    assert is_dup is False
    assert motivo is None


def test_deduplicacao_tipos_diferentes():
    historico = [
        {
            "id": "relato-antigo",
            "timestamp": "2026-11-05T10:00:00Z",
            "tipo": "buraco",
            "latitude": -23.55050,
            "longitude": -46.63330,
            "status": "validado"
        }
    ]

    # Mesmo local, mas problema diferente
    relato_outro_tipo = {
        "id": "relato-outro-tipo",
        "timestamp": "2026-11-07T10:00:00Z",
        "tipo": "obstaculo",
        "latitude": -23.55050,
        "longitude": -46.63330,
        "status": "novo"
    }

    is_dup, motivo = verificar_duplicidade(relato_outro_tipo, historico)
    assert is_dup is False
