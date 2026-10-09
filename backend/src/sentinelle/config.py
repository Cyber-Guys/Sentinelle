from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

RADICE = Path(__file__).resolve().parents[3]  # radice del repository


class Impostazioni(BaseSettings):
    model_config = SettingsConfigDict(env_file=RADICE / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://sentinelle:sentinelle@localhost:5432/sentinelle"
    modalita_offline: bool = False
    cors_origini: list[str] = ["http://localhost:3000"]


impostazioni = Impostazioni()
DIR_OFFLINE = RADICE / "dati" / "offline"
DIR_FOTO = RADICE / "backend" / "foto"
FILE_PESI = RADICE / "backend" / "config" / "pesi.toml"
