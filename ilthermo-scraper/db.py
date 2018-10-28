""" Database engine
"""

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, exists, and_
from sqlalchemy import Column, Integer, Float, Text, Boolean, String, ForeignKey, UniqueConstraint

Base = declarative_base()
metadata = Base.metadata

db_file = 'sqlite:///ilthermo.db'

engine = create_engine(db_file, echo=False)
Session = sessionmaker(engine)
session = Session()


class Property(Base):
    __tablename__ = 'property'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)


class Paper(Base):
    __tablename__ = 'paper'
    id = Column(Integer, primary_key=True)
    year = Column(Integer)
    title = Column(Text, unique=True)
    author = Column(Text)

    datas = relationship('Data', lazy='dynamic')


class DataSet(Base):
    __tablename__ = 'dataset'
    id = Column(Integer, primary_key=True)
    code = Column(String(5))
    searched = Column(Boolean)


class Ion(Base):
    __tablename__ = 'ion'
    id = Column(Integer, primary_key=True)
    charge = Column(Integer)
    name = Column(Text, unique=True)
    searched = Column(Boolean)


class Molecule(Base):
    __tablename__ = 'molecule'
    __table_args__ = (UniqueConstraint('cation_id', 'anion_id', name='ion_id'),)
    id = Column(Integer, primary_key=True)
    code = Column(String(6))
    name = Column(Text, unique=True)
    cation_id = Column(Integer, ForeignKey(Ion.id))
    anion_id = Column(Integer, ForeignKey(Ion.id))
    formula = Column(Text)

    cation = relationship('Ion', foreign_keys='Molecule.cation_id')
    anion = relationship('Ion', foreign_keys='Molecule.anion_id')


class Data(Base):
    __tablename__ = 'data'
    id = Column(Integer, primary_key=True)
    molecule_id = Column(Integer, ForeignKey(Molecule.id))
    paper_id = Column(Integer, ForeignKey(Paper.id))
    property_id = Column(Integer, ForeignKey(Property.id))
    phase = Column(String(20))
    t = Column(Float)
    p = Column(Float, nullable=True)
    value = Column(Float)
    stderr = Column(Float)

    molecule = relationship('Molecule', foreign_keys='Data.molecule_id')
    paper = relationship('Paper', foreign_keys='Data.paper_id')
    property = relationship('Property', foreign_keys='Data.property_id')


metadata.create_all(engine)
