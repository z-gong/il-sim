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
    selected = Column(Boolean, default=False)
    smiles = Column(Text)
    cid = Column(Integer)
    iupac = Column(Text)
    formula = Column(Text)
    validated = Column(Boolean, default=False)
    category = Column(Text)
    popular = Column(Boolean, default=False)
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
    def n_heavy_atoms(self):
        py_mol = pybel.readstring('smi', self.smiles)
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
    selected = Column(Boolean, default=False)
    smiles = Column(Text)
    fit = Column(Text)
    popular = Column(Boolean, default=False)

    cation = relationship('Ion', foreign_keys='Molecule.cation_id')
    anion = relationship('Ion', foreign_keys='Molecule.anion_id')

    datas = relationship('Data', lazy='dynamic')

    def __repr__(self):
        return '<Molecule: %i %s>' % (self.id, self.name)

    def fit_density(self):
        T_list = []
        density_list = []
        density = session.query(Property).filter(Property.name == 'Density').first()
        density_datas = self.datas.filter(Data.property == density).filter(Data.phase == 'Liquid')
        for data in density_datas:
            if data.p == None or data.p < 200:
                T_list.append(data.t)
                density_list.append(data.value)
        if len(T_list) < 5:
            return

        z = np.polyfit(T_list, density_list, 2)
        density_json_dict = {'density': [z[0], z[1], z[2], min(T_list), max(T_list)]}

        fit_json_dict = {}
        if self.fit != None:
            fit_json_dict = json.loads(self.fit)
        fit_json_dict.update(density_json_dict)

        self.fit = json.dumps(fit_json_dict)
        session.commit()

    def fit_st(self):
        T_list = []
        st_list = []
        st_datas = self.datas.join(Property).filter(Property.name == 'Surface tension liquid-gas')
        for data in st_datas:
            T_list.append(data.t)
            st_list.append(data.value)
        if len(T_list) < 5:
            return

        z = np.polyfit(T_list, st_list, 2)
        st_json_dict = {'st': [z[0], z[1], z[2], min(T_list), max(T_list)]}

        fit_json_dict = {}
        if self.fit != None:
            fit_json_dict = json.loads(self.fit)
        fit_json_dict.update(st_json_dict)

        self.fit = json.dumps(fit_json_dict)
        session.commit()

    def get_property(self, prop, T=298):
        try:
            json_dict = json.loads(self.fit)
        except:
            return None

        if prop not in json_dict.keys():
            return None

        a, b, c, Tmin, Tmax = json_dict[prop]
        if T < Tmin - 5 or T > Tmax + 5:
            return None

        return a * T * T + b * T + c

    def get_property_Tmin(self, prop):
        try:
            json_dict = json.loads(self.fit)
        except:
            return None, None

        if prop not in json_dict.keys():
            return None, None

        a, b, c, Tmin, Tmax = json_dict[prop]
        T = Tmin

        return T, a * T * T + b * T + c


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
