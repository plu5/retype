from setup.config.env import iswindows, islinux


to_exclude = []

if iswindows:
    to_exclude = {
        'Qt5DBus.dll', 'opengl32sw.dll', 'Qt5Network.dll', 'Qt5Qml.dll',
        'Qt5QmlModels.dll', 'Qt5Quick.dll', 'Qt5Svg.dll', 'Qt5WebSockets.dll',
        '_bz2', '_hashlib', '_socket', '_ssl', 'libcrypto-1_1.dll',
        'libssl-1_1.dll', 'objectify', 'sax',
    }
elif islinux:
    to_exclude = {
        'libgtk-3', 'libQt5Quick', 'libQt5Qml', 'libcrypto', 'libQt5Network',
        'libQt5WaylandClient', '_decimal', 'libgio-2.0', 'libstdc++', 'libX11',
        'unicodedata', 'pyexpat', 'libglib-2.0', 'libcairo', 'libgcrypt',
        'libepoxy', 'libgdk', 'libkrb5', 'libQt5QmlModels', 'objectify', 'sax',
        'libfreetype', 'libpixman', '_blake2', 'libmirclient', '_pickle',
        '_datetime', '_ctypes', 'libsystemd', '_sha3', 'libharfbuzz',
        'libmirprotobuf', 'libssl', 'libpcre', '_ssl', '_json', 'libgobject',
        '_codecs', 'libprotobuf', 'libpango', 'libdbus', 'libgssapi',
        'libmount', 'libQt5WebSockets', 'libfontconfig', 'libblkid',
        'libxkbcommon', 'libmircommon', '_multibytecodec', '_asyncio',
        'libpng16', '_hashlib', 'libatk', 'libatspi', 'libk5crypto',
        'libglapi', 'libexpat', 'libgraphite', 'libselinux', 'liblzma', '_sha',
        'libxcb', '_csv', 'libz', 'libboost', 'libgcc', '_heapq', '_md5',
        'libpangoft2', 'mmap', 'libgpg', 'libXext', 'libwayland', '_random',
        'libXi', 'termios', '_multiprocessing', '_bisect', 'libgbm', 'grp',
        'libpangocairo', 'resource', '_queue', 'libXrandr', 'libXrender',
        'libXcursor', '_posixshmem', 'libthai', '_statistics', '_opcode',
        'libffi', 'libdatrie', '_contextvars', 'libXxf', 'libXfixes',
        'libXdmcp', 'libuuid', 'libgmodule', 'libkeyutils', 'libcom',
        'libxshmfence', 'libgthread', 'clean', 'diff', 'libXau', 'libXdamage',
        'libXcomposite',
    }


def filterBinaries(toc):
    filtered_binaries = []
    for b in toc:
        matches = [x for x in to_exclude if x in b[0]]
        if not matches:
            filtered_binaries.append(b)

    return filtered_binaries
