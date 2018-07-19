import numpy as np
import requests, pybel, json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Float, Text, Boolean, String, ForeignKey, UniqueConstraint

Base = declarative_base()
metadata = Base.metadata

db_file = 'sqlite:///ilthermo.db?check_same_thread=False'

engine = create_engine(db_file, echo=False)
Session = sessionmaker(engine)
session = Session()


class Property(Base):
    __tablename__ = 'property'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)

    datas = relationship('Data', lazy='dynamic')

    def __repr__(self):
        return '<Property: %i %s>' % (self.id, self.name)


class Paper(Base):
    __tablename__ = 'paper'
    id = Column(Integer, primary_key=True)
    year = Column(Integer)
    title = Column(Text, unique=True)
    author = Column(Text)

    datas = relationship('Data', lazy='dynamic')

    def __repr__(self):
        return '<Paper: %i %s>' % (self.id, self.author)


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
    popular = Column(Boolean, default=False)
    selected = Column(Boolean, default=False)
    smiles = Column(Text)
    iupac = Column(Text)
    ignored = Column('validated', Boolean, default=False)
    duplicate = Column(Integer)
    category = Column(Text)
    n_paper = Column(Integer)
    times = Column(Integer)

    molecules_cation = relationship('Molecule', lazy='dynamic', foreign_keys='Molecule.cation_id')
    molecules_anion = relationship('Molecule', lazy='dynamic', foreign_keys='Molecule.anion_id')

    def __repr__(self):
        if self.charge > 0:
            return '<Ion +%i: %i %s>' % (abs(self.charge), self.id, self.name)
        else:
            return '<Ion -%i: %i %s>' % (abs(self.charge), self.id, self.name)

    @property
    def molecules(self):
        if self.charge > 0:
            return self.molecules_cation
        else:
            return self.molecules_anion

    @property
    def n_heavy(self):
        try:
            py_mol = pybel.readstring('smi', self.smiles)
        except:
            raise Exception('Smiles not valid')
        return py_mol.OBMol.NumHvyAtoms()

    def update_smiles_from_pubchem(self):
        r = requests.get(
            'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/%s/%s/property/IUPACName,CanonicalSMILES,IsomericSMILES,MolecularFormula/JSON'
            % ('name', self.name), timeout=5)
        j = r.json()
        print(j)

        try:
            self.cid = j['PropertyTable']['Properties'][0]['CID']
            self.iupac = j['PropertyTable']['Properties'][0]['IUPACName']
            smiles = j['PropertyTable']['Properties'][0]['CanonicalSMILES']
            py_mol = pybel.readstring('smi', smiles)
            self.smiles = py_mol.write('can').strip()
            self.formula = py_mol.formula
        except Exception as e:
            print(repr(e))

    def update_formula(self):
        self.formula = pybel.readstring('smi', self.smiles).formula


class Molecule(Base):
    __tablename__ = 'molecule'
    __table_args__ = (UniqueConstraint('cation_id', 'anion_id', name='ion_id'),)
    id = Column(Integer, primary_key=True)
    code = Column(String(6))
    name = Column(Text, unique=True)
    cation_id = Column(Integer, ForeignKey(Ion.id))
    anion_id = Column(Integer, ForeignKey(Ion.id))
    formula = Column(Text)
    popular = Column(Boolean, default=False)
    selected = Column(Boolean, default=False)
    fit = Column(Text)

    cation = relationship('Ion', foreign_keys='Molecule.cation_id')
    anion = relationship('Ion', foreign_keys='Molecule.anion_id')

    datas = relationship('Data', lazy='dynamic')

    def __repr__(self):
        return '<Molecule: %i %s>' % (self.id, self.name)


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

    def __repr__(self):
        return '<Data: %s: %.1f %.1f %f>' % (self.property.name, self.t or 0, self.p or 0, self.value)
