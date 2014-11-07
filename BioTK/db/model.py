import os
import uuid

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base, \
    AbstractConcreteBase
from sqlalchemy import Column, Integer, String, LargeBinary, \
    ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref

from .types import UUID

Base = declarative_base()
UUIDColumn = lambda: Column(UUID,
                            primary_key=True,
                            default=uuid.uuid4)

class Entity(AbstractConcreteBase, Base):
    accession = Column(String)
    name = Column(String)

#class Relationship(Base):
#    __tablename__ = "relationship"
#
#    source_id = Column(UUID, ForeignKey("Entity.id"))
#    target_id = Column(UUID, ForeignKey("Entity.id"))

class Taxon(Entity):
    __tablename__ = "taxon"
    __mapper_args__ = {
        "concrete": True,
        "polymorphic_identity": "taxon"
    }

    entity_id = UUIDColumn()

class Gene(Entity):
    __tablename__ = "gene"
    __mapper_args__ = {
        "concrete": True,
        "polymorphic_identity": "gene"
    }

    entity_id = UUIDColumn()
    symbol = Column(String)

class Ontology(Entity):
    __tablename__ = "ontology"
    __mapper_args__ = {
        "concrete": True,
        "polymorphic_identity": "ontology"
    }
    entity_id = UUIDColumn()

class Term(Entity):
    __tablename__ = "term"
    __mapper_args__ = {
        "concrete": True,
        "polymorphic_identity": "term"
    }
    entity_id = UUIDColumn()


###################
# General functions
###################

def get_database_uri_from_configuration():
    from BioTK.config import CACHE_DIR, CONFIG
    try:
        path = os.path.expanduser(CONFIG["database"]["path"])
    except KeyError:
        path = "%s/db.sqlite" % CACHE_DIR
    return "sqlite:///%s" % path

def get_session(uri=None):
    if uri is None:
        uri = get_database_uri_from_configuration()
    engine = create_engine(uri, echo=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return session

if __name__ == "__main__":
    session = get_session()
    g = Gene(accession="5", name="hello")
    session.add(g)
    session.commit()

    #import BioTK.io
    #url = "ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz"
    #with BioTK.io.download(url) as h:
    #    print(next(h))
