# -*- mode: python -*-

def Datafiles(*filenames, **kw):
    import glob
    import os

    def datafile(path, strip_path=False):
        parts = path.split('/')
        path = name = os.path.join(*parts)
        if strip_path:
            name = os.path.basename(path)
        return name, path, 'DATA'

    tmp = list()
    for filename in filenames:
        tmp.extend(glob.glob(filename))

    strip_path = kw.get('strip_path', False)
    return TOC(
        datafile(filename, strip_path=strip_path)
        for filename in tmp
        if os.path.isfile(filename))

a = Analysis(['.\\thisone.py'],
             pathex=['D:\\Documents\\src\\ludumdarewarmup'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\thisone', 'thisone.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=False )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               [('avbin.dll', '.\\avbin.dll', 'BINARY')],
               Datafiles('data/images/girl/*.png', strip_path=False),
               Datafiles('data/images/derp/*.png', strip_path=False),
               Datafiles('data/images/*.png', strip_path=False),
               Datafiles('data/levels/*.json', strip_path=False),
               strip=None,
               upx=True,
               name=os.path.join('dist', 'thisone'))
