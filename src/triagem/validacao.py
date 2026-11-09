import re
import io
import base64
from typing import Tuple, Dict, Any, Union
from pathlib import Path
from PIL import Image

from src.triagem.config import settings

REGEX_CPF = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b')
REGEX_TELEFONE = re.compile(r'\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9?\d{4})[-.\s]?\d{4}\b')


def validar_imagem(imagem: Union[str, bytes]) -> Tuple[bool, str]:
    """
    Valida integridade do buffer de imagem através do Pillow.
    Suporta bytes binários, string base64, caminho local ou URL HTTP/HTTPS.
    Retorna (True, 'OK') ou (False, motivo_erro).
    """
    if not imagem:
        return False, "Imagem não informada ou vazia"

    try:
        buffer: bytes = b""
        if isinstance(imagem, bytes):
            buffer = imagem
        elif isinstance(imagem, str):
            if imagem.startswith("http://") or imagem.startswith("https://"):
                import requests
                resp = requests.get(imagem, timeout=30)
                if resp.status_code != 200:
                    return False, f"Falha ao baixar imagem: HTTP {resp.status_code}"
                buffer = resp.content
            elif Path(imagem).is_file():
                buffer = Path(imagem).read_bytes()
            else:
                # Trata possíveis cabeçalhos data:image/...;base64,
                raw = imagem.split(",", 1)[1] if "," in imagem else imagem
                buffer = base64.b64decode(raw)

        if not buffer:
            return False, "Buffer de imagem vazio"

        with Image.open(io.BytesIO(buffer)) as img:
            img.verify()  # Valida integridade do arquivo
            
        # Reabre para verificar dimensões
        with Image.open(io.BytesIO(buffer)) as img:
            largura, altura = img.size
            if largura < 10 or altura < 10:
                return False, f"Dimensões insuficientes ({largura}x{altura})"

        return True, "Imagem válida"
    except Exception as e:
        return False, f"Imagem corrompida ou formato inválido: {str(e)}"


def validar_coordenadas_sp(latitude: float, longitude: float) -> Tuple[bool, str]:
    """
    Verifica se a coordenada informada está contida na Bounding Box do município de São Paulo.
    """
    min_lat, max_lat, min_lon, max_lon = settings.sp_bounding_box
    if not (min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon):
        return False, f"Coordenadas ({latitude}, {longitude}) fora da Bounding Box de SP"
    return True, "Coordenadas dentro dos limites de SP"


def mascarar_lgpd(texto: str) -> str:
    """
    Aplica expressões regulares para ofuscar dados pessoais (CPF e Telefone) em conformidade com a LGPD.
    """
    if not texto:
        return ""
    texto_anonimizado = REGEX_CPF.sub("***.***.***-**", texto)
    texto_anonimizado = REGEX_TELEFONE.sub("(**) *****-****", texto_anonimizado)
    return texto_anonimizado


def sanitizar_relato_lgpd(relato: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gera uma cópia segura do relato mascarando CPF, telefone e descrição para relatórios e logs.
    """
    relato_seguro = dict(relato)
    if "autor_cpf" in relato_seguro and relato_seguro["autor_cpf"]:
        relato_seguro["autor_cpf"] = mascarar_lgpd(str(relato_seguro["autor_cpf"]))
    if "autor_telefone" in relato_seguro and relato_seguro["autor_telefone"]:
        relato_seguro["autor_telefone"] = mascarar_lgpd(str(relato_seguro["autor_telefone"]))
    if "descricao" in relato_seguro and relato_seguro["descricao"]:
        relato_seguro["descricao"] = mascarar_lgpd(str(relato_seguro["descricao"]))
    # Anonimiza nome se presente
    if "autor_nome" in relato_seguro and relato_seguro["autor_nome"]:
        partes = str(relato_seguro["autor_nome"]).strip().split()
        if len(partes) > 1:
            relato_seguro["autor_nome"] = f"{partes[0]} {partes[-1][0]}."
        else:
            relato_seguro["autor_nome"] = f"{partes[0][0]}***"
    return relato_seguro
