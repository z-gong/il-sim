#!/usr/bin/env python3

from ilthermo.models import *

mols = session.query(Molecule)
mols_popular = mols.filter(Molecule.popular == True)

density = session.query(Property).filter(Property.name == 'Density').first()
hvap = session.query(Property).get(16)


def print_value(mol, T, P, val):
    print('%i %s.%s %i %i %.3f 1.0 %s %s %s %s %s' % (
        mol.id, mol.cation.smiles, mol.anion.smiles, T, P, val, mol.cation.smiles, mol.anion.smiles,
        mol.cation.category, mol.anion.category, mol.name.replace(' ', '_')))


def get_density():
    for mol in mols_popular:
        den = mol.get_property('density', T=298)
        if den != None:
            print_value(mol, 298, 1, den / 1000)

    print('')
    for mol in mols_popular:
        den = mol.get_property('density', T=298)
        if den == None:
            T, den = mol.get_property_Tmin('density')
            if T != None:
                print_value(mol, T, 1, den / 1000)

    print('')
    for mol in mols_popular:
        den = mol.get_property('density', T=298)
        if den == None:
            T, den = mol.get_property_Tmin('density')
            if T == None:
                datas = mol.datas.filter(Data.property == density).filter(Data.phase == 'Liquid').all()
                datas.sort(key=lambda x: abs(x.t - 298))
                if datas != []:
                    data = datas[0]
                    print_value(mol, int(data.t), int(data.p / 100), data.value / 1000)


def get_hvap():
    for mol in mols_popular:
        datas = mol.datas.filter(Data.property == hvap).order_by(Data.t).all()
        if datas != []:
            data = datas[0]
            print_value(mol, int(data.t), 1, data.value)


if __name__ == '__main__':
    get_density()
    # get_hvap()
