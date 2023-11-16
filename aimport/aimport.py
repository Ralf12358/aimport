import sys, os, pathlib


"""
Guido views running scripts within a package as an anti-pattern:
    rejected PEP-3122: https://www.python.org/dev/peps/pep-3122/#id1

I disagree. This is an ugly workaround.
"""


def add(pa=sys.path[0], pa2=None):
    if os.path.isfile(pa):
        pa = os.path.dirname(pa)

    if not pa2 is None:
        if os.path.isfile(pa2):
            pa2 = os.path.dirname(pa2)
        pa = os.path.join(pa, pa2)

    add = [pa]
    while True:
        if pathlib.Path((os.path.join(pa, "__init__.py"))).exists():
            add.append(pa)
        pn = os.path.dirname(pa)
        if pn == pa:
            break
        pa = pn

    tmp = add + sys.path
    sys.path = []
    for e in tmp:
        if not e in sys.path:
            sys.path.append(e)
    # print(f"sys.path: {sys.path}")


add()
