from starlette.testclient import TestClient
from src.triagem.servidor_mock import app


def test_mock_server_saude():
    client = TestClient(app)
    resp = client.get("/saude")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["modo_fake"] is True


def test_mock_server_assistente_perguntas_sugeridas():
    client = TestClient(app)

    # 1. Buraco
    resp1 = client.post("/assistente", json={"pergunta": "Como peço o conserto de um buraco na calçada?"})
    assert resp1.status_code == 200
    dados1 = resp1.json()
    assert dados1["recusou"] is False
    assert len(dados1["fontes"]) > 0

    # 2. Responsável pela calçada
    resp2 = client.post("/assistente", json={"pergunta": "Quem é responsável pela calçada em frente a uma casa?"})
    assert resp2.status_code == 200
    dados2 = resp2.json()
    assert "15.442" in dados2["resposta"]
    assert dados2["recusou"] is False

    # 3. Vaso bloqueando
    resp3 = client.post("/assistente", json={"pergunta": "Tem um vaso bloqueando a calçada, o que eu faço?"})
    assert resp3.status_code == 200
    dados3 = resp3.json()
    assert dados3["recusou"] is False

    # 4. Carro na calçada (recusa oficial orientando CET)
    resp4 = client.post("/assistente", json={"pergunta": "Como reclamar de um carro estacionado na calçada?"})
    assert resp4.status_code == 200
    dados4 = resp4.json()
    assert dados4["recusou"] is True


def test_mock_server_visao_deteccao():
    client = TestClient(app)
    resp = client.post("/deteccoes", files={"imagem": ("buraco.jpg", b"fakebytes", "image/jpeg")})
    assert resp.status_code == 200
    deteccoes = resp.json()
    assert isinstance(deteccoes, list)
    assert len(deteccoes) == 1
    assert deteccoes[0]["classe"] == "buraco"
