import os
from datetime import datetime

from . import data


datas = data.datas_tuples


def saveDateToFile(path, file_name="builddate.txt"):
    file_path = os.path.join(path, file_name)
    date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%fZ")
    if os.path.exists(path):
        with open(file_path, 'w') as f:
            f.write(date)

    return datas + [(file_path, 'include')]
