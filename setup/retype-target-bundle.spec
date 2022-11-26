# -*- mode: python ; coding: utf-8 -*-
import os
from setup.config import data, binaries, imports, version, builddate


version_str = version.getVersionStr(os.path.abspath("."))

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
               name=data.name + 'bundle-coll')

app = BUNDLE(coll,  # noqa: F821
             name=data.name + '.app',
             icon=data.icns,
             bundle_identifier=data.name,
             info_plist={"CFBundleExecutable": "MacOS/retype",
                         "NSPrincipalClass": "NSApplication",
                         "LSBackgroundOnly": "0",
                         "LSMinimumSystemVersion": "10.9.0",
                         "CFBundleShortVersionString": version_str})
