# -*- mode: python -*-

def Datafiles(*filenames, **kw):
    import os

    def datafile(path, strip_path=False):
        parts = path.split('/')
        path = name = os.path.join(*parts)
        if strip_path:
            name = os.path.basename(path)
        return name, path, 'DATA'

    strip_path = kw.get('strip_path', False)
    return TOC(
        datafile(filename, strip_path=strip_path)
        for filename in filenames
        if os.path.isfile(filename))

a = Analysis(['.\\launcher.py'],
             pathex=['D:\\Documents\\src\\ludumdarewarmup'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\launcher', 'launcher.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=False )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               [('avbin.dll', '.\\avbin.dll', 'BINARY')],
#               Datafiles('data/images/sq.png', strip_path=False),
#               Datafiles('data/sounds/move.wav', strip_path=False),
               strip=None,
               upx=True,
               name=os.path.join('dist', 'launcher'))
