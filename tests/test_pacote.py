import csv
from pathlib import Path
from src.triagem.pacote import gerar_pacotes_despacho
from src.triagem.config import settings


def test_gerar_pacotes_despacho_append_e_consolidacao(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "dist_dir", tmp_path / "pacotes")

    data_teste = "2026-11-09"

    # Lote 1: 2 chamados da Sé
    lote1 = [
        {
            "id": "relato-001",
            "timestamp": "2026-11-09T08:00:00Z",
            "status": "validado",
            "subprefeitura": "Sé",
            "distrito": "República",
            "tipo": "buraco",
            "prioridade": "ALTA",
            "latitude": -23.543,
            "longitude": -46.641,
            "descricao": "Buraco grande na calçada",
            "motivo_decisao": "Próximo a sinistro"
        },
        {
            "id": "relato-002",
            "timestamp": "2026-11-09T08:15:00Z",
            "status": "encaminhado",
            "subprefeitura": "Sé",
            "distrito": "Bela Vista",
            "tipo": "desnivel",
            "prioridade": "NORMAL",
            "latitude": -23.555,
            "longitude": -46.650,
            "descricao": "Desnível acentuado",
            "motivo_decisao": "Fluxo padrão"
        }
    ]

    res1 = gerar_pacotes_despacho(lote1, data_lote=data_teste)
    assert "Sé" in res1
    assert res1["Sé"]["total_itens"] == 2
    assert Path(res1["Sé"]["csv"]).exists()
    assert Path(res1["Sé"]["pdf"]).exists()

    # Lote 2: Mais 1 chamado novo da Sé (30 min depois) + 1 repetido (já despachado)
    lote2 = [
        {
            "id": "relato-001",  # repetido
            "timestamp": "2026-11-09T08:00:00Z",
            "status": "validado",
            "subprefeitura": "Sé",
            "distrito": "República",
            "tipo": "buraco",
            "prioridade": "ALTA",
            "latitude": -23.543,
            "longitude": -46.641,
            "descricao": "Buraco grande",
            "motivo_decisao": "Repetido"
        },
        {
            "id": "relato-003",  # novo
            "timestamp": "2026-11-09T08:30:00Z",
            "status": "validado",
            "subprefeitura": "Sé",
            "distrito": "Sé",
            "tipo": "obstaculo",
            "prioridade": "BAIXA",
            "latitude": -23.550,
            "longitude": -46.633,
            "descricao": "Poste inclinado",
            "motivo_decisao": "Via local"
        }
    ]

    res2 = gerar_pacotes_despacho(lote2, data_lote=data_teste)
    assert res2["Sé"]["total_itens"] == 3  # 2 anteriores + 1 novo (deduplicou relato-001)

    # Verifica se o CSV tem exatamente 3 registros
    caminho_csv = res2["Sé"]["csv"]
    with open(caminho_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 3
        ids = [r["id_relato"] for r in reader]
        assert ids == ["relato-001", "relato-002", "relato-003"]
        for r in reader:
            assert "data_hora_registro" in r
            assert "horario_triagem_rpa" in r
            assert len(r["data_hora_registro"]) > 0
            assert len(r["horario_triagem_rpa"]) > 0

    # Verifica se o PDF foi recriado com sucesso e tem tamanho válido
    caminho_pdf = res2["Sé"]["pdf"]
    assert caminho_pdf.exists()
    assert caminho_pdf.stat().st_size > 1000
