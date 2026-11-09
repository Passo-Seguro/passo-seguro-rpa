import pytest
import io
import base64
from PIL import Image


@pytest.fixture
def imagem_valida_base64():
    """Gera um buffer de imagem JPEG válido codificado em base64."""
    img = Image.new("RGB", (50, 50), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@pytest.fixture
def imagem_invalida_base64():
    """Buffer de base64 corrompido que não constitui imagem válida."""
    return "ABC_NOT_AN_IMAGE_BUFFER_CORRUPT_DATA=="


@pytest.fixture
def relato_valido_se(imagem_valida_base64):
    """Relato válido localizado na Sé."""
    return {
        "id": "relato-teste-se",
        "timestamp": "2026-11-07T12:00:00Z",
        "tipo": "buraco",
        "descricao": "Buraco no piso perto da Praça da Sé.",
        "latitude": -23.5505,
        "longitude": -46.6333,
        "imagem_base64": imagem_valida_base64,
        "autor_nome": "Cidadão Teste",
        "autor_cpf": "123.456.789-00",
        "autor_telefone": "(11) 98765-4321",
        "status": "novo",
        "visao": {
            "classe": "buraco",
            "confianca": 0.95
        }
    }
