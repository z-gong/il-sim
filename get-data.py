#!/usr/bin/env python3

from ilthermo.models import *
from sqlalchemy import or_

mols = session.query(Molecule)
mols_selected = mols.filter(Molecule.selected == True)

density = session.query(Property).filter(Property.name == 'Density').first()
hvap = session.query(Property).get(16)
viscosity = session.query(Property).filter(Property.name == 'Viscosity').first()


def print_value(mol, T, P, val):
    print('%i %s.%s %i %i %.3f 1.0 %s %s %s %s %s' % (
        mol.id, mol.cation.smiles, mol.anion.smiles, T, P, val, mol.cation.smiles, mol.anion.smiles,
        mol.cation.category, mol.anion.category, mol.name.replace(' ', '_')))


def get_density_fitted(Tden):
    for mol in mols_selected:
        den = mol.get_property('density', T=Tden)
        if den != None:
            print_value(mol, Tden, 1, den / 1000)

    print('')
    for mol in mols_selected:
        den = mol.get_property('density', T=Tden)
        if den == None:
            T, den = mol.get_property_Tmax('density')
            if T != None:
                print_value(mol, T, 1, den / 1000)

    print('')
    for mol in mols_selected:
        den = mol.get_property('density', T=Tden)
        if den == None:
            T, den = mol.get_property_Tmax('density')
            if T == None:
                datas = mol.datas.filter(Data.property == density).filter(Data.phase == 'Liquid').all()
                datas.sort(key=lambda x: abs(x.t - Tden))
                if datas != []:
                    data = datas[0]
                    print_value(mol, int(data.t), int((data.p or 100) / 100), data.value / 1000)


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


if __name__ == '__main__':
    get_density(343)
    get_hvap()
    # get_viscosity(343)
