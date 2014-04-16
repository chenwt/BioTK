from sqlalchemy.ext.declarative import declarative_base

class Taxon(Base):
    __tablename__ = "taxon"
    id = Column(Integer, primary_key=True)

class Platform(Base):
    __tablename__ = "platform"
    id = Column(Integer, primary_key=True)
    title = Column(String())
    manufacturer = Column(String())
    taxon_id = Column(Integer, ForeignKey("taxon.id"))

from sqlalchemy import create_engine

def connect():
    engine = create_engine("postgresql://gilesc@localhost:5432/BioTK")
    Base.metadata.create_all(engine)
