import sys
import os


subdir = 'include'

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), subdir))
sys._MEIPASS = os.path.join(sys._MEIPASS, subdir)
