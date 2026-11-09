import pytest
import requests
import responses
from src.triagem.cliente_api import ClienteAPI


@responses.activate
def test_resiliencia_visao_503_tres_tentativas_e_degradacao_suave():
    """
    Verifica que se a API de visão computacional responder com HTTP 503,
    o cliente tenta exatamente 3 vezes com retry e depois degrada suavemente retornando None.
    """
    url_visao = "http://visao.test/deteccoes"
    responses.add(
        responses.POST,
        url_visao,
        status=503
    )

    cliente = ClienteAPI(vision_api_url=url_visao, mock_mode=False)
    # Reduz tempos de espera no teste para ser veloz
    resultado = cliente.solicitar_deteccao_visao("base64dummydata")

    assert len(responses.calls) == 3
    assert resultado is None


@responses.activate
def test_visao_sucesso_retorna_payload():
    """Verifica chamada bem sucedida ao serviço de visão computacional."""
    url_visao = "http://visao.test/deteccoes"
    responses.add(
        responses.POST,
        url_visao,
        json={"classe": "buraco", "confianca": 0.92},
        status=200
    )

    cliente = ClienteAPI(vision_api_url=url_visao, mock_mode=False)
    resultado = cliente.solicitar_deteccao_visao("base64dummydata")

    assert len(responses.calls) == 1
    assert resultado == {"classe": "buraco", "confianca": 0.92}


@responses.activate
def test_buscar_relatos_retry_e_falha():
    """Verifica que a busca de relatos retenta 3 vezes antes de levantar exceção de conexão."""
    url_api = "http://api.test/relatos"
    responses.add(
        responses.GET,
        url_api,
        status=500
    )

    cliente = ClienteAPI(api_base_url="http://api.test", mock_mode=False)

    with pytest.raises(requests.RequestException):
        cliente.buscar_relatos_novos(pagina=1)

    assert len(responses.calls) == 3
