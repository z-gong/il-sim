#!/usr/bin/env python3

from ilthermo.models import *

ions = session.query(Ion).filter(Ion.validated == True).all()
ions.sort(key=lambda x: x.molecules.count(), reverse=True)
print(len(ions))

unique_ions = {}
for ion in ions:
    smiles = ion.smiles
    if smiles not in unique_ions.keys():
        unique_ions[smiles] = ion
    else:
        ion_eq = unique_ions[smiles]
        print(ion, ion_eq)
        for mol in ion.molecules:
            if ion.charge > 0:
                mol.cation_id = ion_eq.id
            else:
                mol.anion_id = ion_eq.id
        session.delete(ion)

try:
    session.commit()
except:
    session.rollback()
    raise

print(len(unique_ions))
