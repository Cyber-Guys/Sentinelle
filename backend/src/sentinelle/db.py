from sqlalchemy import create_engine

from .config import impostazioni

engine = create_engine(impostazioni.database_url, pool_pre_ping=True)
