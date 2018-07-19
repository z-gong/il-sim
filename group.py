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
        '[n+]1ccnc1': 'cIm',
        '[n+]1ccccc1': 'cPy',
        '[N+]1CCCC1': 'cPyrr',
        'C1CCCC[NX4+]1': 'cN4pi',
        '[NX4+]': 'cN4',
        '[PX4+]': 'cP4',
        'N~[C+](~N)~N': 'cGua',
        'S(=O)(=O)[N-]S(=O)(=O)': 'aSI',
        '[B-]C#N': 'aNC[B]',
        '[C-]C#N': 'aNC[C]',
        '[N-]C#N': 'aNC[N]',
        '[S-]C#N': 'aNC[S]',
        '[Cl-]': 'a0Cl',
        '[Br-]': 'a0Br',
        '[I-]': 'a0I',
        '[O-]c1ccccc1': 'aPhO',
        'C(=O)[O-]': 'aCO2',
        '[!O]S(=O)(=O)[O-]': 'aSO3',
        'OS(=O)(=O)[O-]': 'aSO4',
        '[O-][N+](=O)[O-]': 'aNO3',
        '[O-][Cl](=O)(=O)=O': 'aClO4',
        '[O-]P(=O)': 'aPO2',
        '[BX4-]': 'aXB4',
        '[PX6-]': 'aXP6',
    }
    for ion in session.query(Ion).filter(Ion.ignored==False):
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
