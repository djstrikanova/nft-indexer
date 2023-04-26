from sqlalchemy import Column, Integer, String, BigInteger, UniqueConstraint, JSON, DateTime, func
from config.database import Base

class NFT(Base):
    __tablename__ = "nfts"

    asset_id = Column(String, primary_key=True)
    collection_name = Column(String, nullable=False)
    schema_name = Column(String, nullable=False)
    template_id = Column(Integer, nullable=False)
    asset_immutable_data = Column(JSON, nullable=False)
    template_immutable_data = Column(JSON, nullable=False)
    last_updated = Column(DateTime, default=func.now(), nullable=False)

    def __init__(self, asset_id, collection_name, schema_name, template_id, asset_immutable_data,template_immutable_data):
        self.asset_id = asset_id
        self.collection_name = collection_name
        self.schema_name = schema_name
        self.template_id = template_id
        self.asset_immutable_data = asset_immutable_data
        self.template_immutable_data = template_immutable_data
