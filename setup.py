import os
import sys
import shutil
import optparse
import PyInstaller.__main__


build_dir = './build'
dist_dir = './dist'


def option_parser():
    parser = optparse.OptionParser()
    parser.add_option(
        '-c',
        '--clean',
        default=False,
        action='store_true',
        help=('rm dist and build folders'))
    parser.add_option(
        '-o',
        '--onefile',
        default=False,
        action='store_true',
        help=('Build into one executable'))
    parser.add_option(
        '-x',
        '--hacky',
        default=False,
        action='store_true',
        help=('Hacky onedir build that moves dependencies to a subfolder.\
 Requires adding to pyinstaller pyimod03_importers.py\
 `sys._MEIPASS = pyi_os_path.os_path_join(sys._MEIPASS, "include")`')
    )
    return parser


def main(args=sys.argv):
    parser = option_parser()
    opts, args = parser.parse_args(args)
    opts.cli_args = args[2:]

    if opts.clean:
        if os.path.exists(build_dir):
            print(f'Deleting {build_dir}')
            shutil.rmtree('./build')
        if os.path.exists(dist_dir):
            print(f'Deleting {dist_dir}')
            shutil.rmtree('./dist')
        return 0
    elif opts.onefile:
        PyInstaller.__main__.run(['./setup/retype-target-onefile.spec'])
    elif opts.hacky:
        PyInstaller.__main__.run(['./setup/retype-target-hacky.spec'])
        source_dir = dist_dir + '/retype'
        sub_dir = source_dir + '/include'
        file_names = os.listdir(source_dir)
        exclude = {'base_library.zip', 'python37.dll',
                   'icons', 'library', 'style', 'retype.exe', 'include'}
        os.makedirs(sub_dir, exist_ok=True)
        for f in file_names:
            if f not in exclude:
                shutil.move(os.path.join(source_dir, f),
                            os.path.join(sub_dir, f))
    else:  # normal build
        PyInstaller.__main__.run(['./setup/retype-target.spec'])

    return 0


if __name__ == '__main__':
    sys.exit(main())
