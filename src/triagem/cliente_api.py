import logging
import base64
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log

from src.triagem.config import settings

logger = logging.getLogger("triagem.cliente_api")


class ClienteAPI:
    """
    Cliente de integração HTTP com a API principal do Passo Seguro e o serviço de Visão Computacional.
    Conecta-se à API em produção (Azure Container Apps) ou local, com suporte a autenticação Bearer
    e resiliência via Exponential Backoff (tenacity).
    Também opera em Modo Mock 100% autônomo e offline quando as APIs na nuvem estiverem desativadas.
    """

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        vision_api_url: Optional[str] = None,
        service_token: Optional[str] = None,
        vision_token: Optional[str] = None,
        mock_mode: Optional[bool] = None,
        mock_data_path: Optional[Path] = None
    ):
        self.api_base_url = (api_base_url or settings.api_base_url).rstrip("/")
        self.vision_api_url = (vision_api_url or settings.vision_api_url).rstrip("/")
        self.service_token = service_token or settings.service_token
        self.vision_token = vision_token or settings.vision_token
        self.mock_mode = settings.mock_mode if mock_mode is None else mock_mode
        self.mock_data_path = Path(mock_data_path or settings.mock_data_path)
        self._mock_relatos: List[Dict[str, Any]] = []

        if self.mock_mode:
            self.carregar_dados_mock()

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.service_token:
            headers["Authorization"] = f"Bearer {self.service_token}"
        return headers

    def carregar_dados_mock(self):
        """Carrega os relatos simulados do arquivo local de mock. Se não existir, inicializa com lote_demo.json."""
        if self.mock_data_path.exists():
            try:
                with open(self.mock_data_path, "r", encoding="utf-8") as f:
                    self._mock_relatos = json.load(f)
                return
            except Exception as e:
                logger.warning(f"Erro ao ler mock_data_path: {e}. Inicializando com lote_demo.json")

        origem = Path("tests/fixtures/lote_demo.json")
        if origem.exists():
            self.mock_data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(origem, "r", encoding="utf-8") as f_origem:
                self._mock_relatos = json.load(f_origem)
            try:
                with open(self.mock_data_path, "w", encoding="utf-8") as f_dest:
                    json.dump(self._mock_relatos, f_dest, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def resetar_dados_mock(self):
        """Reseta todos os relatos mock para o status inicial 'novo'."""
        origem = Path("tests/fixtures/lote_demo.json")
        if origem.exists():
            with open(origem, "r", encoding="utf-8") as f:
                self._mock_relatos = json.load(f)
            self.mock_data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.mock_data_path, "w", encoding="utf-8") as f:
                json.dump(self._mock_relatos, f, ensure_ascii=False, indent=2)

    def set_mock_data(self, relatos: List[Dict[str, Any]]):
        """Define os dados simulados quando executando em modo mock/demonstração."""
        self.mock_mode = True
        self._mock_relatos = [dict(r) for r in relatos]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(requests.RequestException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    def buscar_relatos_novos(self, pagina: int = 1, tamanho: int = 50) -> List[Dict[str, Any]]:
        """
        Busca novos relatos pendentes de triagem com retentativas automáticas.
        Consome GET /relatos?status=novo&pagina={pagina} na API real.
        """
        if self.mock_mode:
            # Retorna todos os que estiverem com status "novo"
            return [r for r in self._mock_relatos if r.get("status") == "novo"]

        url = f"{self.api_base_url}/relatos"
        params = {"status": "novo", "pagina": pagina, "tamanho": tamanho}
        resposta = requests.get(url, params=params, headers=self._headers(), timeout=45)
        resposta.raise_for_status()
        dados = resposta.json()
        itens = dados.get("itens", []) if isinstance(dados, dict) else dados

        # Normaliza campos do contrato oficial (lat -> latitude, lon -> longitude, categoria -> tipo)
        relatos_normalizados = []
        for item in itens:
            r = dict(item)
            r["id"] = str(item.get("id"))
            r["latitude"] = item.get("lat", item.get("latitude"))
            r["longitude"] = item.get("lon", item.get("longitude"))
            r["tipo"] = item.get("categoria") or item.get("tipo", "outro")
            r["descricao"] = item.get("descricao") or ""
            relatos_normalizados.append(r)

        return relatos_normalizados

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(requests.RequestException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        retry_error_callback=lambda retry_state: None
    )
    def solicitar_deteccao_visao(self, imagem: Union[str, bytes]) -> Optional[Dict[str, Any]]:
        """
        Submete imagem ao modelo de visão computacional (YOLO) via POST /deteccoes.
        Envia multipart/form-data com o campo 'imagem', conforme contrato do passo-seguro-visao.
        Degradação suave: se a API estiver fora do ar após 3 tentativas, retorna None.
        """
        if self.mock_mode:
            classe_sugerida = "buraco"
            confianca = 0.88
            if isinstance(imagem, str):
                img_lower = imagem.lower()
                if "piso" in img_lower or "rachad" in img_lower:
                    classe_sugerida = "piso_danificado"
                    confianca = 0.82
                elif "obstaculo" in img_lower or "entulho" in img_lower:
                    classe_sugerida = "obstaculo"
                    confianca = 0.79
                elif "veiculo" in img_lower or "carro" in img_lower:
                    classe_sugerida = "veiculo_na_calcada"
                    confianca = 0.95
                elif "sem_defeito" in img_lower:
                    return None
            return {
                "classe": classe_sugerida,
                "confianca": confianca,
                "caixa": {"x": 0.20, "y": 0.35, "largura": 0.35, "altura": 0.28},
                "todas": [{"classe": classe_sugerida, "confianca": confianca}]
            }

        img_bytes: bytes = b""
        if isinstance(imagem, bytes):
            img_bytes = imagem
        elif isinstance(imagem, str):
            if imagem.startswith("http://") or imagem.startswith("https://"):
                r = requests.get(imagem, timeout=10)
                if r.status_code == 200:
                    img_bytes = r.content
            elif Path(imagem).is_file():
                img_bytes = Path(imagem).read_bytes()
            else:
                raw = imagem.split(",", 1)[1] if "," in imagem else imagem
                try:
                    # Adiciona padding se faltar
                    padding = len(raw) % 4
                    if padding != 0:
                        raw_padded = raw + "=" * (4 - padding)
                    else:
                        raw_padded = raw
                    img_bytes = base64.b64decode(raw_padded)
                except Exception:
                    img_bytes = raw.encode("utf-8")

        if not img_bytes:
            return None

        token = self.vision_token or self.service_token
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        files = {"imagem": ("foto.jpg", img_bytes, "image/jpeg")}
        resposta = requests.post(
            self.vision_api_url,
            files=files,
            headers=headers,
            timeout=30
        )
        resposta.raise_for_status()
        deteccoes = resposta.json()
        if isinstance(deteccoes, list) and len(deteccoes) > 0:
            top = deteccoes[0]
            return {
                "classe": top.get("classe"),
                "confianca": top.get("confianca", 1.0),
                "caixa": top.get("caixa"),
                "todas": deteccoes
            }
        elif isinstance(deteccoes, dict):
            return deteccoes
        return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(requests.RequestException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    def atualizar_status_relato(
        self,
        id_relato: str,
        novo_status: str,
        motivo: str = "",
        prioridade: Optional[str] = None,
        subprefeitura: Optional[str] = None,
        dados_complementares: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Atualiza o status de um relato na API principal via PATCH /relatos/{id}.
        Adere estritamente ao contrato AtualizacaoRelato da API.
        """
        payload: Dict[str, Any] = {
            "status": novo_status
        }
        if prioridade:
            prio = prioridade.lower()
            if prio == "normal":
                prio = "media"
            if prio in ["alta", "media", "baixa"]:
                payload["prioridade"] = prio

        if subprefeitura and subprefeitura not in ["Outras_Regioes", "Não Identificado"]:
            payload["subprefeitura"] = subprefeitura

        if self.mock_mode:
            atualizou = False
            for r in self._mock_relatos:
                if str(r.get("id")) == str(id_relato):
                    r.update(payload)
                    r["motivo_triagem"] = motivo
                    if dados_complementares:
                        r.update(dados_complementares)
                    atualizou = True
                    break
            if atualizou and self.mock_data_path:
                try:
                    with open(self.mock_data_path, "w", encoding="utf-8") as f:
                        json.dump(self._mock_relatos, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return atualizou

        url = f"{self.api_base_url}/relatos/{id_relato}"
        resposta = requests.patch(url, json=payload, headers=self._headers(), timeout=45)
        resposta.raise_for_status()
        return True
