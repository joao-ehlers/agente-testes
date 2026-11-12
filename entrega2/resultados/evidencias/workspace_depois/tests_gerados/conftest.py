import os, sys
raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (raiz, os.path.join(raiz, 'src'), os.path.join(raiz, 'lib')):
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
