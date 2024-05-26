import os

from setup.config.env import iswindows, islinux, ismacos


s_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

to_exclude = []
to_add = []

if iswindows:
    to_exclude = {
        'Qt5DBus.dll', 'opengl32sw.dll', 'Qt5Network.dll', 'Qt5Qml.dll',
        'Qt5QmlModels.dll', 'Qt5Quick.dll', 'Qt5Svg.dll', 'Qt5WebSockets.dll',
        '_bz2', '_socket', '_ssl', 'libcrypto-1_1.dll', 'libssl-1_1.dll',
        'objectify', 'sax', 'core-libraryloader',
    }
elif islinux:
    to_exclude = {
        'libgtk-3', 'libQt5Quick', 'libQt5Qml', 'libcrypto', 'libQt5Network',
        'libQt5WaylandClient', '_decimal', 'libgio-2.0', 'libstdc++', 'libX11',
        'unicodedata', 'pyexpat', 'libglib-2.0', 'libcairo', 'libgcrypt',
        'libepoxy', 'libgdk', 'libkrb5', 'libQt5QmlModels', 'objectify', 'sax',
        'libfreetype', 'libpixman', 'libmirclient', '_pickle',
        '_datetime', '_ctypes', 'libsystemd', 'libharfbuzz',
        'libmirprotobuf', 'libssl', 'libpcre', '_ssl', '_json', 'libgobject',
        '_codecs', 'libprotobuf', 'libpango', 'libdbus', 'libgssapi',
        'libmount', 'libQt5WebSockets', 'libfontconfig', 'libblkid',
        'libxkbcommon', 'libmircommon', '_multibytecodec', '_asyncio',
        'libpng16', 'libatk', 'libatspi', 'libk5crypto',
        'libglapi', 'libexpat', 'libgraphite', 'libselinux', 'liblzma',
        'libxcb', '_csv', 'libz', 'libboost', 'libgcc', '_heapq',
        'libpangoft2', 'mmap', 'libgpg', 'libXext', 'libwayland',
        'libXi', 'termios', '_multiprocessing', '_bisect', 'libgbm', 'grp',
        'libpangocairo', 'resource', '_queue', 'libXrandr', 'libXrender',
        'libXcursor', '_posixshmem', 'libthai', '_statistics', '_opcode',
        'libffi', 'libdatrie', '_contextvars', 'libXxf', 'libXfixes',
        'libXdmcp', 'libuuid', 'libgmodule', 'libkeyutils', 'libcom',
        'libxshmfence', 'libgthread', 'clean', 'diff', 'libXau', 'libXdamage',
        'libXcomposite',
    }
    to_add = [
        {'from': s_dir + '/plugins/libcomposeplatforminputcontextplugin.so',
         'to': 'PyQt5/Qt5/plugins/platforminputcontexts/\
libcomposeplatforminputcontextplugin.so'},
        {'from': s_dir + '/plugins/libfcitxplatforminputcontextplugin.so',
         'to': 'PyQt5/Qt5/plugins/platforminputcontexts/\
libfcitxplatforminputcontextplugin.so'}
    ]
elif ismacos:
    to_exclude = {
        'libcrypto', 'libncursesw', 'libssl', 'QtNetwork', 'QtQml', 'QtQuick',
        'QtSvg', 'QtWebSockets', 'objectify', 'sax', '_bisect',
        '_bz2', '_codecs', '_ctypes', '_datetime', '_heapq',
        '_json', '_lzma', '_multibyte', '_opcode', '_pickle',
        '_scproxy', '_socket', '_ssl', '_uuid', 'grp',
        'pyexpat', 'readline', 'resource', 'termios', 'unicodedata',
    }


def filterBinaries(toc):
    filtered_binaries = []
    for b in toc:
        matches = [x for x in to_exclude if x in b[0]]
        if not matches:
            filtered_binaries.append(b)

    added_binaries = []
    for b in to_add:
        added_binaries.append((b['to'], b['from'], 'BINARY'))

    return added_binaries + filtered_binaries
