# -*- mode: python ; coding: utf-8 -*-
import os
from setup.config import data, binaries, imports, builddate


datas = builddate.saveDateToFile(os.path.abspath("."))

a = Analysis(['../retype-target.py'],  # noqa: F821
             pathex=[],
             binaries=[],
             datas=datas,
             hiddenimports=imports.addn,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=['./setup/subdir-hook.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             noarchive=False)

a.binaries -= [(os.path.normcase(x), None, None) for x in binaries.to_exclude]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)  # noqa: F821

exe = EXE(pyz,  # noqa: F821
          a.scripts,
          [],
          exclude_binaries=True,
          name=data.name,
          icon=data.icon,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None)

coll = COLLECT(exe,  # noqa: F821
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name=data.name + '-hacky')
