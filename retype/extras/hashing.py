import os
import hashlib


def generate_file_md5(path, blocksize=2**20):
    """https://stackoverflow.com/a/1131255"""
    m = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()
