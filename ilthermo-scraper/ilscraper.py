#! /usr/bin/env python3

import sys
import requests 
import json
import re
import time
from queue import Queue
from db import *
from ionname import split_molecule


root_url = 'http://ilthermo.boulder.nist.gov'

class Log:
    logfile = open('ilscraper-%s.log' % time.strftime('%y%m%d-%H%M%S'), 'w')
    
    @staticmethod
    def write(*args, **kwargs):
        print(*args, **kwargs, file=sys.stderr)
        print(*args, **kwargs, file=Log.logfile)
    
    @staticmethod
    def flush():
        Log.logfile.flush()


class SearchFailedError(Exception):
    def __init__(self):
        super().__init__()


class SpecialCaseError(Exception):
    def __init__(self, args=None):
        super().__init__(args)


def get_page(url, params={}, try_times=5):
    while try_times > 0:
        try:
            r = requests.get(url, params=params)
            break 
        except ConnectionError:
            Log.write('Connection error. trying...')
            try_times -= 1

    if try_times <= 0:
        raise ConnectionAbortedError()
        return None
    else:
        return r.text


def add_or_query(row, unique_key):
    
    filter_dict = {unique_key: row.__dict__[unique_key]}

    result = session.query(row.__class__).filter_by(**filter_dict).first()
    if not result:
        session.add(row)
        session.flush()
    else:
        row.id = result.id 


def get_prp_table(prp_url, try_times=5):
    """ Get property --> prpcode table.
    """
    try:
        prp_table_raw = get_page(prp_url, try_times=try_times)
    except ConnectionAbortedError:
        Log.write('Cannot get prp table. Using local version instead...')
        prp_table_raw = ''.join([line for line in open('ilprpls.json', 'r').readlines()])   # using local version instead

    prp_table_json = json.loads(prp_table_raw)
    prp_table = {}

    for plist in prp_table_json['plist']:
        prp_table.update(dict(zip(plist['name'], plist['key'])))

    return prp_table


def get_paper_table(search_url, params, try_times=5):
    """ Return formatted paper table.
    """
    try:
        search_result_raw = get_page(search_url, params, try_times)
    except ConnectionAbortedError:
        Log.write('Search failed')
        raise SearchFailedError()

    search_result_json = json.loads(search_result_raw)

    try:
        data_header = search_result_json['header']
    except KeyError:
        Log.write('No result:', search_url)
        raise SearchFailedError()

    code_idx = data_header.index('setid')
    ref_idx = data_header.index('ref')
    prp_idx = data_header.index('prp')
    phase_idx = data_header.index('phases')
    cmp_idx = data_header.index('cmp1')
    cmpname_idx = data_header.index('nm1')

    paper_table = []

    for line in search_result_json['res']:
        paper_table.append({
            'code': line[code_idx],
            'ref': line[ref_idx],
            'molecule_code': line[cmp_idx],
            'molecule': line[cmpname_idx],
            'property': line[prp_idx],
            'phase': line[phase_idx],
        })

    return paper_table


def get_data_table(search_url, params, try_times=5):
    
    parse_success = False 

    while not parse_success:

        try:
            search_result_raw = get_page(search_url, params, try_times)
        except ConnectionAbortedError:
            Log.write('Get data failed')
            raise SearchFailedError()

        try:
            search_data = json.loads(search_result_raw)
            parse_success = True 
        except json.JSONDecodeError:
            Log.write('Cannot parse. Try downloading again...')


    paper_info = {
        'title': search_data['ref']['title'], 
        'author': search_data['ref']['full']
        }
    paper_year_str = re.search('(19\d\d)|(20\d\d)', paper_info['author']).group()
    try:
        paper_info['year'] = int(paper_year_str)
    except ValueError:
        Log.write('Cannot convert year:', paper_year_str)
        raise SpecialCaseError()

    molecule_info = {
        'name': search_data['components'][0]['name'], 
        'formula': re.sub('\</?SUB\>', '', search_data['components'][0]['formula'])
        }
        
    try:
        molecule_info['cation'], molecule_info['anion'] = split_molecule(molecule_info['name'])
    except AssertionError:
        Log.write('Cannot split molecule:', molecule_info['name'])
        raise SpecialCaseError()
    
    # return data info: list[t, p, value, err]
    units = [u[0] for u in search_data['dhead']]
    if len(units) > 3:
        Log.write('Not equal 2 condition:', units)
        raise SpecialCaseError()
    p_idx = None 
    t_idx = None
    data_table = []
    for i in range(len(units) - 1):
        if units[i] == "Temperature, K":
            t_idx = i
        elif units[i] == "Pressure, kPa":
            p_idx = i
        else:
            print('Unit unrecognizable:', units[i])
            raise SpecialCaseError()

    def get_prp(line, idx):
        if idx is not None:
            return line[idx][0]
        else:
            return None

    for line in search_data['data']:
        data_table.append([
            get_prp(line, t_idx),
            get_prp(line, p_idx),
            line[-1][0],
            line[-1][1]
        ])
    
    return paper_info, molecule_info, data_table


def put_prp_table(prp_table):
    
    prp_table_tuple = [i for i in prp_table.items()]
    prp_table_tuple.sort(key=lambda x:x[0])     # sort by name, alphabet order

    if not session.query(Property).first():   # table exists
           
        session.bulk_save_objects([
            Property(name=line[0]) for line in prp_table_tuple
        ])
        session.commit()

        return dict([(row[0], i) for row, i in zip(prp_table_tuple, range(len(prp_table_tuple)))]) # name-->idx
    else:
        prps = session.query(Property).all()

        return dict([(prp.name, prp.id) for prp in prps])


def put_ion(name, charge):
    ion = Ion(charge=charge, name=name, searched=False)
    add_or_query(ion, 'name')


def put_molecule(molecule_info):
    
    cation = session.query(Ion).filter_by(name=molecule_info['cation']).first()
    anion = session.query(Ion).filter_by(name=molecule_info['anion']).first()
    
    molecule = Molecule(
        code=molecule_info['code'],
        name=molecule_info['name'],
        cation_id=cation.id, 
        anion_id=anion.id, 
        formula=molecule_info['formula'])
    add_or_query(molecule, 'name')

    molecule_info['id'] = molecule.id
    

def put_paper(paper_info):
    
    paper = Paper(
        year=paper_info['year'], 
        title=paper_info['title'],
        author=paper_info['author'])

    add_or_query(paper, 'title')
    paper_info['id'] = paper.id 


def put_data(data_table, paper_info, molecule_id):
    
    data = []
    for line in data_table:
        data.append(Data(
            molecule_id=molecule_id,
            paper_id=paper_info['id'],
            property_id=paper_info['property_id'],
            phase=paper_info['phase'], # check phase string first!
            t=line[0],
            p=line[1],
            value=line[2],
            stderr=line[3]
        ))
    
    session.bulk_save_objects(data) 


def main():
    
    # First we get table
    prp_table = get_prp_table(root_url + '/ILT2/ilprpls')
    prp_index = put_prp_table(prp_table)

    search_history = set() # set of ions searched
    search_history.update([ion.name for ion in session.query(Ion).all()])

    search_queue = Queue()
    exist_ions = [ion.name for ion in session.query(Ion).filter_by(searched=False)]
    if exist_ions:
        list(map(search_queue.put, exist_ions))
    else:
        try:
            mol_list = open('complex_mol.txt', 'r')
            for line in mol_list:
                cation, anion = split_molecule(line.rstrip('\n'))
                put_ion(cation, 1)
                put_ion(anion, -1)
                search_queue.put(cation)
                search_queue.put(anion)
        except IOError:
            search_queue.put('fluoride')
            put_ion('fluoride', -1)

    session.commit()

    while not search_queue.empty():
        print('There are %d species in queue' % search_queue.qsize())
        search_name = search_queue.get()
        print('Search species:', search_name)

        try:
            paper_table = get_paper_table(root_url + '/ILT2/ilsearch', params={
                'cmp': search_name, 
                'ncmp': 1,
                'year': '',
                'auth': '',
                'keyw': '',
                'prp': ''
                })
        except SearchFailedError:
            Log.write('Cannot search. Skip this...')
            continue
        except SpecialCaseError:
            Log.write('Special case error. Skip this...')
            continue

        print('Get %d papers, ' % len(paper_table), end='')

        paper_table_new = []
        for line in paper_table:
            if not session.query(exists().where(and_(DataSet.code == line['code'], DataSet.searched == True))).scalar():
                paper_table_new.append(line)
                session.add(DataSet(code=line['code'], searched=False))

        session.commit()
        paper_table = paper_table_new
        print('%d need to be downloaded' % len(paper_table))

        for idx, line in enumerate(paper_table):
            if session.query(DataSet).filter_by(code=line['code']).first().searched:
                continue

            print('[%d%%] Search paper %s (%s)...' % (idx*100/len(paper_table), line['code'], line['ref']), end='')

            try:
                paper_info, molecule_info, data_table = get_data_table(root_url + '/ILT2/ilset', params={'set': line['code']})
            except SearchFailedError:
                Log.write('Cannot get data from paper. Skipping...')
                continue
            except SpecialCaseError:
                Log.write('Cannot read data from paper properly. Skipping...')
                continue 
            
            session.query(DataSet).filter_by(code=line['code']).update({DataSet.searched: True})

            paper_info['phase'] = line['phase']
            paper_info['property_id'] = prp_index[line['property']]
            paper_info['molecule'] = line['molecule']
            molecule_info['code'] = line['molecule_code']

            print('Get %d data points' % len(data_table))

            if not session.query(Ion).filter_by(name=molecule_info['cation']).first():
                search_queue.put(molecule_info['cation'])
                put_ion(molecule_info['cation'], 1)
            if not session.query(Ion).filter_by(name=molecule_info['anion']).first():
                search_queue.put(molecule_info['anion'])
                put_ion(molecule_info['anion'], -1)

            put_molecule(molecule_info)
            put_paper(paper_info)

            if len(data_table) > 20:
                session.commit()

            put_data(data_table, paper_info, molecule_info['id'])
            session.commit()


            session.commit()
            Log.flush()

        session.query(Ion).filter_by(name=search_name).update({Ion.searched: True})
        session.commit()
        print('\n')

    print('Finished')
    return


if __name__ == '__main__':
    main()