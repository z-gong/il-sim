#!/usr/bin/env python3

from ilthermo.models import *
from sqlalchemy import or_

mols = session.query(Molecule)
mols_selected = mols.filter(Molecule.selected == True)

density = session.query(Property).filter(Property.name == 'Density').first()
viscosity = session.query(Property).filter(Property.name == 'Viscosity').first()
cp = session.query(Property).filter(Property.name == 'Heat capacity at constant pressure').first()
diffusion = session.query(Property).filter(Property.name == 'Self-diffusion coefficient').first()
hvap = session.query(Property).filter(Property.name == 'Enthalpy of vaporization or sublimation').first()


def print_value(mol, T, P, val):
    print('%i %s.%s %i %i %.3f 1.0 %s %s %s %s %s' % (
        mol.id, mol.cation.smiles, mol.anion.smiles, T, P, val, mol.cation.smiles, mol.anion.smiles,
        mol.cation.category, mol.anion.category, mol.name.replace(' ', '_')))


def get_hvap():
    for mol in mols_selected:
        datas = mol.datas.filter(Data.property == hvap).order_by(Data.t).all()
        if datas != []:
            data = datas[0]
            print_value(mol, int(data.t), 0, data.value)


def get_density(T):
    for mol in mols_selected:
        datas = mol.datas.filter(Data.property == density) \
            .filter(Data.phase == 'Liquid') \
            .filter(or_(Data.p == None, Data.p < 200)) \
            .all()
        datas.sort(key=lambda x: abs(x.t - T))
        if datas != []:
            data = datas[0]
            P = int(data.p / 100) if data.p != None else 1
            print_value(mol, int(data.t), P, data.value / 1000)


def get_viscosity(T):
    for mol in mols_selected:
        datas = mol.datas.filter(Data.property == viscosity) \
            .filter(Data.phase == 'Liquid') \
            .filter(or_(Data.p == None, Data.p < 200)) \
            .all()
        datas.sort(key=lambda x: abs(x.t - T))
        if datas != []:
            data = datas[0]
            P = int(data.p / 100) if data.p != None else 1
            print_value(mol, int(data.t), P, data.value * 1000)


def get_cp(T):
    for mol in mols_selected:
        datas = mol.datas.filter(Data.property == cp) \
            .filter(Data.phase == 'Liquid') \
            .filter(or_(Data.p == None, Data.p < 200)) \
            .all()
        datas.sort(key=lambda x: abs(x.t - T))
        if datas != []:
            data = datas[0]
            P = int(data.p / 100) if data.p != None else 1
            print_value(mol, int(data.t), P, data.value)


def get_diffusion(T):
    for mol in mols_selected:
        datas = mol.datas.filter(Data.property == diffusion) \
            .filter(Data.phase == 'Liquid') \
            .filter(or_(Data.p == None, Data.p < 200)) \
            .all()
        datas.sort(key=lambda x: abs(x.t - T))
        if datas != []:
            data = datas[0]
            P = int(data.p / 100) if data.p != None else 1
            print_value(mol, int(data.t), P, data.value)


if __name__ == '__main__':
    get_density(343)
    # get_viscosity(343)
    # get_cp(343)
    # get_diffusion(343)
    # get_hvap()
