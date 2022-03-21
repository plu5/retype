import sys
import os


subdir_name = 'include'
subdir_path = os.path.join(os.path.dirname(sys.executable), subdir_name)

sys.path.append(subdir_path)
