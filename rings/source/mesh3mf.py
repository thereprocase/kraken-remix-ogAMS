"""Load vertices and triangles of one object from a 3MF file."""
import re
import zipfile

import numpy as np

VERT = re.compile(rb'<vertex x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"')
TRI = re.compile(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"')
OBJ = re.compile(rb'<object id="(\d+)"[^>]*>(.*?)</object>', re.S)


def load(path, oid="1"):
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith(".model"):
                for i, body in OBJ.findall(z.read(n)):
                    if i.decode() == str(oid):
                        v = np.array(VERT.findall(body), dtype=float)
                        t = np.array(TRI.findall(body), dtype=np.int64)
                        return v, t
    raise KeyError(oid)

