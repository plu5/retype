# -*- mode: python ; coding: utf-8 -*-
import os
from setup.config import data, binaries, imports, builddate, util

from PyInstaller.config import CONF


datas = builddate.saveDateToFile(os.path.abspath("."))

a = Analysis(['../retype-target.py'],  # noqa: F821
             pathex=[],
             binaries=[],
             datas=datas,
             hiddenimports=imports.addn,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             noarchive=False)

a.binaries = binaries.filterBinaries(a.binaries)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)  # noqa: F821

# Split datas to ones meant to be included in the exe and ones not
unbundled_data = []
bundled_data = []
for (dest, source, kind) in a.datas:
    root_subdir = util.getRoot(dest)
    if (root_subdir in data.folder_names):
        unbundled_data.append((dest, source, kind))
    else:
        bundled_data.append((dest, source, kind))

old_distpath = CONF['distpath']
CONF['distpath'] = CONF['workpath']

exe = EXE(pyz,  # noqa: F821
          a.scripts,
          a.binaries,
          a.zipfiles,
          bundled_data,
          [],
          name=os.path.join(workpath, data.name),  # noqa: F821
          icon=data.icon,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None)

CONF['distpath'] = old_distpath

coll = COLLECT(exe,  # noqa: F821
               unbundled_data,
               name=data.name + '-onefile')
