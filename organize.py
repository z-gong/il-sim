#!/usr/bin/env python3

from ilthermo.models import *


def process_unique():
    ions = session.query(Ion).filter(Ion.smiles != None).all()
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
            # session.delete(ion)

    try:
        session.commit()
    except:
        session.rollback()
        raise

    print(len(unique_ions))


def process_category():
    category_smarts = {
        '[n+]1ccnc1': 'imidazolium',
        '[n+]1ncnc1': 'triazolium',
        '[n+]1ccccc1': 'pyridinium',
        '[N+]1CCCC1': 'pyrrolidinium',
        '[NX4+]': 'N4+',
        '[PX4+]': 'P4+',
        'N~[C+](~N)~N': 'guanidinium',
        'S(=O)(=O)[N-]S(=O)(=O)': 'sulfonylimide',
        '[n-]1ccnn1': 'triazolide',
        'c1cn[n-]c1': 'pyrazolide',
        '[B-]C#N': 'NC[B-]',
        '[C-]C#N': 'NC[C-]',
        '[N-]C#N': 'NC[N-]',
        '[S-]C#N': 'NC[S-]',
        '[Cl-]': 'Cl-',
        '[Br-]': 'Br-',
        '[I-]': 'I-',
        '[O-]c1ccccc1': 'PhO-',
        'C(=O)[O-]': 'CO2-',
        'S(=O)(=O)[O-]': 'SO3-',
        '[O-][N+](=O)[O-]': 'NO3-',
        '[O-][Cl](=O)(=O)=O': 'ClO4-',
        '[O-]P(=O)(O)O': 'H2PO4-',
        '[BX4-]': 'B4-',
        '[PX6-]': 'P6-',
    }
    for ion in session.query(Ion).filter(Ion.smiles != None):
        ion.category = None
        py_mol = pybel.readstring('smi', ion.smiles)
        for smarts, category in category_smarts.items():
            s = pybel.Smarts(smarts)
            if s.findall(py_mol).__len__() > 0:
                ion.category = category
                print(ion, category)
                break

    try:
        session.commit()
    except:
        session.rollback()
        raise


if __name__ == '__main__':
    # process_unique()
    process_category()
