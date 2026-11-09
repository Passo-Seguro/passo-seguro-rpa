from src.triagem.prioridade import (
    avaliar_prioridade_e_status,
    verificar_proximidade_infosiga
)


def test_gateway1_baixa_confianca_visao(relato_valido_se):
    # Confiança 0.40 (< 0.60) deve desviar para revisão humana
    visao_baixa = {"classe": "buraco", "confianca": 0.40}
    status, prioridade, just = avaliar_prioridade_e_status(relato_valido_se, visao_baixa)
    assert status == "revisao_humana"
    assert "Baixa confiança" in just


def test_gateway2_proximidade_infosiga_prioridade_alta():
    # Coordenada na Praça da Sé (onde temos o sinistro fatal INF-2026-001)
    relato_se = {
        "id": "relato-se-critico",
        "tipo": "buraco",
        "latitude": -23.5505,
        "longitude": -46.6333
    }
    visao_alta = {"classe": "buraco", "confianca": 0.95}
    status, prioridade, just = avaliar_prioridade_e_status(relato_se, visao_alta)
    assert status == "validado"
    assert prioridade == "ALTA"
    assert "sinistro de trânsito" in just.lower()


def test_gateway2_sem_sinistro_prioridade_normal():
    # Local sem atropelamento recente catalogado
    relato_normal = {
        "id": "relato-sem-sinistro",
        "tipo": "piso_danificado",
        "latitude": -23.5900,
        "longitude": -46.6800
    }
    visao_ok = {"classe": "piso_danificado", "confianca": 0.85}
    status, prioridade, just = avaliar_prioridade_e_status(relato_normal, visao_ok)
    assert status == "validado"
    assert prioridade == "NORMAL"
