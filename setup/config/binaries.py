import os

from setup.config.env import iswindows, islinux, ismacos


s_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

to_exclude = []
to_add = []

if iswindows:
    to_exclude = {
    }
elif islinux:
    to_exclude = {
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
