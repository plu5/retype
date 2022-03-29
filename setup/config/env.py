from sys import platform


iswindows = platform.lower() in ['win32', 'win64']
ismacos = 'darwin' in platform.lower()
islinux = not(iswindows or ismacos)

