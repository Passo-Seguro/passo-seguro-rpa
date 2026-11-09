from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Tuple, Optional
from pathlib import Path

class Settings(BaseSettings):
    """Configurações da esteira de automação do Passo Seguro RPA."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    api_base_url: str = "https://ca-passoseguro-app.ashysea-c9ccc16b.centralus.azurecontainerapps.io/api"
    vision_api_url: str = "https://visao-production-e222.up.railway.app/deteccoes"
    service_token: Optional[str] = None
    vision_token: Optional[str] = None

    geosampa_data_path: Path = Path("data/geosampa_subprefeituras.geojson")
    infosiga_csv_path: Path = Path("data/infosiga_sinistros.csv")
    intervalo_execucao_minutos: int = 30
    log_level: str = "INFO"
    dist_dir: Path = Path("dist/pacotes")
    
    # Bounding Box do Município de São Paulo: (min_lat, max_lat, min_lon, max_lon)
    sp_bounding_box: Tuple[float, float, float, float] = (-24.0, -23.3, -46.9, -46.3)

    # Limiares de Regra de Negócio
    raio_deduplicacao_metros: float = 30.0
    janela_deduplicacao_dias: int = 14
    raio_infosiga_metros: float = 150.0
    limiar_confianca_visao: float = 0.60

settings = Settings()
