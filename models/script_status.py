from sqlalchemy import Column, Integer, String, DateTime,func
from config.database import Base

class ScriptStatus(Base):
    __tablename__ = "script_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False,default=func.now(),onupdate=func.now())

    def __init__(self, key, value):
        self.key = key
        self.value = value