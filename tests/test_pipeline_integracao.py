import json
from pathlib import Path
from src.triagem.cliente_api import ClienteAPI
from src.triagem.main import processar_lote_triagem, JSONLinesLogger


def test_pipeline_integracao_lote_demo(tmp_path):
    # Carrega os 10 relatos demo
    with open("tests/fixtures/lote_demo.json", "r", encoding="utf-8") as f:
        dados_demo = json.load(f)

    cliente = ClienteAPI()
    cliente.set_mock_data(dados_demo)

    logger = JSONLinesLogger(log_dir=tmp_path / "logs")
    historico = []

    resultado = processar_lote_triagem(cliente, logger, historico)
    metricas = resultado["metricas"]

    # Verificações da esteira
    assert metricas["processados"] == 10
    assert metricas["encaminhados"] == 6
    assert metricas["revisao_humana"] == 1
    assert metricas["duplicados"] == 1
    assert metricas["rejeitados"] == 3  # foto inválida + fora de SP + duplicado
    assert metricas["erros"] == 0

    # Verifica se os pacotes foram criados
    pacotes = resultado["pacotes"]
    assert len(pacotes) > 0
    for sub, info in pacotes.items():
        assert Path(info["csv"]).exists()
        assert Path(info["pdf"]).exists()
