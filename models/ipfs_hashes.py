from sqlalchemy import Column, String, Text, DateTime, func, JSON, Integer, BigInteger
from config.database import Base

class HashTable(Base):
    __tablename__ = "hash_table"

    ipfs_hash = Column(String, primary_key=True)
    content_description = Column(JSON, nullable=True, default=None)
    file_type = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)
    timeouts = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=func.now(),onupdate=func.now(), nullable=False)
    file_size = Column(BigInteger, nullable=True)

    def __init__(self, ipfs_hash, meta, content_description=None, file_type=None, file_path=None, timeouts=0, file_size=None):
        self.ipfs_hash = ipfs_hash
        self.content_description = content_description
        self.meta = meta
        self.file_type = file_type
        self.file_path = file_path
        self.timeouts = timeouts
        self.file_size = file_size