#!/usr/bin/env python3

from ilthermo.models import *

ions = session.query(Ion).filter(Ion.selected == True).filter(Ion.smiles != None)
for ion in ions:
    m = pybel.readstring('smi', ion.smiles)
    # prefix = 'C' if ion.charge > 0 else 'A'
    prefix = ion.category
    m.write('svg', 'svg/%s_%03i.svg' % (prefix, ion.id), overwrite=True)
    m.addh()
    m.make3D()
    m.write('mol2', 'mol2/%s_%03i.mol2' % (prefix, ion.id), overwrite=True)

ions = session.query(Ion).filter(Ion.popular == True).filter(Ion.smiles != None)
for ion in ions:
    break
    m = pybel.readstring('smi', ion.smiles)
    # prefix = 'C' if ion.charge > 0 else 'A'
    prefix = ion.category
    m.write('svg', 'svg-pop/%s-%03i.svg' % (prefix, ion.id), overwrite=True)
    m.addh()
    m.make3D()
    m.write('mol2', 'mol2-pop/%s-%03i.mol2' % (prefix, ion.id), overwrite=True)
