""" Deal with molecule information
"""
import re 

def format_organic(name):
    
    if name.endswith('-,') or name.endswith('-') or name.endswith('yl,'):
        
        splitstr = name.split()
        assert len(splitstr) == 2
        return splitstr[1].rstrip(',') + splitstr[0].rstrip(',')
    else:
        return re.sub('- ', '-', name)


def split_molecule(name):
    """Return cation, Anion"""

    name = re.sub(' \(\d:\d\)', '', name)
    name = re.sub(' Chemical.*', '', name)
    splitstr = name.split(' ')
    if len(splitstr) == 2:
        return splitstr[0], splitstr[1]

    # salt ?
    salt_pos = re.search('salt', name)
    if salt_pos:
        if re.search('salt with', name):
            return format_organic(name[:salt_pos.span()[0] - 1]), name[salt_pos.span()[0] + 10:]
        else:
            assert splitstr[-1] == 'salt'
            return splitstr[-2], ' '.join(splitstr[:-2]).rstrip(',')

    # end with e?
    assert name[-1] == 'e'
    if len(splitstr) >= 3:
        if splitstr[-1] == 'carboxylate' or splitstr[-2].endswith('yl') or splitstr[-2].endswith('hydrogen') or splitstr[-2] == 'bis':
            return format_organic(' '.join(splitstr[:-2])), ' '.join(splitstr[-2:])
        else:
            return format_organic(' '.join(splitstr[:-1])), splitstr[-1]

    # single word
    organ_anion_pos = re.search('\w-\d', name)
    if organ_anion_pos:
        return name[:organ_anion_pos.span()[0] + 1], name[organ_anion_pos.span()[1] - 1:]

    ium_pos = re.search('ium', name)
    assert ium_pos
    return name[:ium_pos.span()[1]], name[ium_pos.span()[1]:]
        
