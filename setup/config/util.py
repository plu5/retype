import os


def getRoot(path):
    root = os.path.split(path)[0]
    while True:
        split = os.path.split(root)[0]
        if split == '':
            break
        root = split
    return root
