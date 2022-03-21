import os
import shutil
from textwrap import wrap
from setuptools import Command

has_pyinstaller = False

try:
    import PyInstaller.__main__
    has_pyinstaller = True
except ModuleNotFoundError:
    has_pyinstaller = False


build_dir = './build'
dist_dir = './dist'


build_kinds = {
    'onedir': 'Normal build',
    'onefile': 'Build into one executable',
    'hacky': 'Hacky onedir build that moves dependencies to a subfolder.\
 Requires adding to pyinstaller pyimod03_importers.py\
 `sys._MEIPASS = pyi_os_path.os_path_join(sys._MEIPASS, "include")`'
}


def helpForArgsdict(argsdict, line_length=80, key_len=12,
                    prelog='Optional arguments:'):
    val_len = line_length - key_len
    output = prelog + '\n'
    for key, value in argsdict.items():
        output += '\n' + key + (key_len-len(key)) * ' '
        output += '\n'.join(
            wrap(value, val_len, subsequent_indent=(key_len * ' ')))
    return output


def build(kind):
    if not has_pyinstaller:
        print('Could not import PyInstaller')
        return 1
    if kind == 'onedir':
        PyInstaller.__main__.run(['./setup/retype-target.spec'])
    elif kind == 'onefile':
        PyInstaller.__main__.run(['./setup/retype-target-onefile.spec'])
    elif kind == 'hacky':
        PyInstaller.__main__.run(['./setup/retype-target-hacky.spec'])
        source_dir = dist_dir + '/retype-hacky'
        sub_dir = source_dir + '/include'
        qtlib_dir = sub_dir + '/PyQt5/Qt5/lib'
        file_names = os.listdir(source_dir)
        exclude = {'base_library.zip', 'python3',
                   'icons', 'library', 'style', 'retype', 'include',
                   '_struct', 'zlib'}
        os.makedirs(sub_dir, exist_ok=True)
        for f in file_names:
            matches = [x for x in exclude if x in f]
            if not matches:
                if f.startswith('libQt5') or f in \
                   ['libicuuc.so.56', 'libicui18n.so.56', 'libicudata.so.56']:
                    os.makedirs(qtlib_dir, exist_ok=True)
                    shutil.move(os.path.join(source_dir, f),
                                os.path.join(qtlib_dir, f))
                else:
                    shutil.move(os.path.join(source_dir, f),
                                os.path.join(sub_dir, f))
    else:
        print('Undefined build kind')


def clean():
    if os.path.exists(build_dir):
        print(f'Deleting {build_dir}')
        shutil.rmtree('./build')
    if os.path.exists(dist_dir):
        print(f'Deleting {dist_dir}')
        shutil.rmtree('./dist')


class b(Command):
    """Build retype executables with pyinstaller"""
    description = 'Build retype executables with pyinstaller'
    user_options = [
        ('kind=', 'k', f'the kind of build to make\
 (out of {", ".join(list(build_kinds.keys()))})'),
        ('clean', 'c', 'rm build and dist folders'),
        ('xhelp', 'x', 'show help message and exit. can also be run by running\
 command with no arguments.')
    ]
    boolean_options = ['clean', 'xhelp']

    user_options_dict = {}
    for t in user_options:
        user_options_dict[f'-{t[1]}, --{t[0]}'] = t[2]

    def initialize_options(self):
        self.kind = None
        self.clean = False
        self.xhelp = False

    def finalize_options(self):
        if self.kind is not None and self.kind not in build_kinds:
            raise Exception("Undefined build kind")

    def run(self):
        if self.kind:
            build(self.kind)
        elif self.clean:
            clean()
        else:
            output = helpForArgsdict(self.user_options_dict, key_len=15)
            output += '\n\n' + helpForArgsdict(
                build_kinds, prelog='Build kinds available:')
            print(output)
