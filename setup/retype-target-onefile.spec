# -*- mode: python ; coding: utf-8 -*-
import os
from setup.config import data, binaries, imports


a = Analysis(['../retype-target.py'],  # noqa: F821
             pathex=[],
             binaries=[],
             datas=data.datas_tuples,
             hiddenimports=imports.addn,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             noarchive=False)

a.binaries -= [(os.path.normcase(x), None, None) for x in binaries.to_exclude]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)  # noqa: F821

# Split datas to ones meant to be included in the exe and ones not
unbundled_data = []
bundled_data = []
for (dest, source, kind) in a.datas:
    if os.path.split(dest)[0] in data.folder_names:
        unbundled_data.append((dest, source, kind))
    else:
        bundled_data.append((dest, source, kind))

exe = EXE(pyz,  # noqa: F821
          a.scripts,
          a.binaries,
          a.zipfiles,
          bundled_data,
          [],
          name=data.name,
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

coll = COLLECT(exe,  # noqa: F821
               unbundled_data,
               name=data.name + '-onefile')
