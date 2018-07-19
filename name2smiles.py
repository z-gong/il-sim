#!/usr/bin/env python3

import os
import time
from ilthermo.models import *
from pubchempy import get_compounds, get_properties
from chemspipy import ChemSpider

cs_token = os.environ['CHEMSPIDER_TOKEN']
cs = ChemSpider(cs_token)

ions = session.query(Ion)
n = 0
for ion in ions.filter(Ion.smiles == None):
    MATCHED = False
    pc_d_list = get_properties('IUPACName,IsomericSMILES,CanonicalSMILES', ion.name, 'name')
    print('PubChem: ', ion, pc_d_list)
    if len(pc_d_list) == 1:
        d = pc_d_list[0]
        iupac = d.get('IUPACName')
        smiles = d.get('IsomericSMILES') or d.get('CanonicalSMILES')
        MATCHED = True

    if not MATCHED:
        cs_results = cs.search(ion.name)
        cs_results.wait()
        print('ChemSpider: ', ion, cs_results)
        if len(cs_results) == 1:
            result = cs_results[0]
            iupac = None
            smiles = result.smiles
            MATCHED = True

    if MATCHED:
        m = pybel.readstring('smi', smiles)
        # Neutral species, obviously wrong
        if m.charge != 0:
            ion.iupac = iupac
            ion.smiles = m.write('can').strip()

    n += 1
    if n % 10 == 0:
        session.commit()

    time.sleep(0.5)

session.commit()
