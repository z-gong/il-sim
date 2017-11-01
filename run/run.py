#!/usr/bin/env python3

import os, sys, shutil
from collections import OrderedDict

CWD = os.path.dirname(os.path.abspath(__file__))


class MacConfig:
    PACKMOL_BIN = '/Users/zheng/Projects/DFF/Developing/bin64m/Packmol/packmol.exe'
    GMX_BIN = '/opt/gromacs/2016.3/bin/gmx'
    DFF_ROOT = '/Users/zheng/Projects/DFF/Developing'
    DFF_TABLE = 'TEAM_IL'

    MS_TOOLS_DIR = os.path.join(CWD, '../../ms-tools')

    PBS_MANAGER = 'local'
    PBS_QUEUE_DICT = OrderedDict([(None, 2)])

    WORK_DIR = '/tmp/ILs'


class ClusterConfig:
    PACKMOL_BIN = '/share/apps/tools/packmol'
    GMX_BIN = '/share/apps/gromacs/2016.3/bin/gmx_gpu'
    DFF_ROOT = '/share/apps/dff/msdserver'
    DFF_TABLE = 'TEAM_IL'

    MS_TOOLS_DIR = '/home/gongzheng/GitHub/ms-tools'

    PBS_MANAGER = 'torque'
    PBS_QUEUE_DICT = OrderedDict([('gtx', 2)])
    PBS_ENV_CMD = 'export MALLOC_CHECK_=0'

    WORK_DIR = '/home/gongzheng/workspace/ILs/MD'


Config = MacConfig

sys.path.append(Config.MS_TOOLS_DIR)

from mstools.simulation.gmx import Npt
from mstools.jobmanager import Torque, Local
from mstools.utils import cd_or_create_and_cd

if Config.PBS_MANAGER == 'torque':
    jobmanager = Torque(queue_dict=Config.PBS_QUEUE_DICT, env_cmd=Config.PBS_ENV_CMD)

elif Config.PBS_MANAGER == 'local':
    jobmanager = Local(queue_dict=Config.PBS_QUEUE_DICT)

kwargs = {'packmol_bin': Config.PACKMOL_BIN, 'dff_root': Config.DFF_ROOT, 'dff_table': Config.DFF_TABLE,
          'gmx_bin': Config.GMX_BIN, 'jobmanager': jobmanager}

npt = Npt(**kwargs)


class Target():
    def __init__(self, name, cation, anion, T, density):
        self.name = name
        self.cation = cation
        self.anion = anion
        self.T = T
        self.density = density


if __name__ == '__main__':
    CWD = os.getcwd()
    gtx_dirs = []
    cmd = sys.argv[1]

    targets = []
    for line in open(sys.argv[2]):
        if line.strip() != '' and not line.startswith('#'):
            words = line.strip().split()
            _name = words[0]
            _cation = words[1]
            _anion = words[2]
            _d300 = words[3]
            _d350 = words[4]
            if _d300 != 'None':
                targets.append(Target(_name, _cation, _anion, 300, float(_d300)))
            if _d350 != 'None':
                targets.append(Target(_name, _cation, _anion, 350, float(_d350)))

    if cmd == 'npt':
        for target in targets:
            dir_base = os.path.join(Config.WORK_DIR, 'NPT/%s' % target.name)
            dir_run = os.path.join(dir_base, '%i' % target.T)
            cd_or_create_and_cd(dir_base)
            npt.set_system([target.cation, target.anion], 3000, nmol_list=[1, 1], density=target.density * 0.9 / 1000)
            if not os.path.exists('init.msd'):
                npt.build()

            cd_or_create_and_cd(dir_run)
            shutil.copy('../conf.gro', '.')
            shutil.copy('../topol.top', '.')
            shutil.copy('../topol.itp', '.')
            gtx_cmds = npt.prepare(T=target.T, P=1, dt=0.002, nst_eq=int(3E5), nst_run=int(5E5),
                                   jobname='npt-%s-%i' % (target.name, target.T))
            gtx_dirs.append(os.path.abspath(dir_run))
            os.chdir(CWD)

        commands_list = npt.gmx.generate_gpu_multidir_cmds(gtx_dirs, gtx_cmds)
        for i, commands in enumerate(commands_list):
            sh = os.path.join(CWD, '_job.npt-%i.sh' % i)
            jobmanager.generate_sh(CWD, commands, name='NPT-GTX-%i' % i, sh=sh)
            jobmanager.submit(sh)
