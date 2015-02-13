# -*- mode: python -*-
version = open(os.path.join("tools", "version.txt"), 'r').read().strip()
##### include tools in distribution #######
def extra_datas(mydir,exclude=[]):
    def rec_glob(p, files):
        import os
        import glob
        for d in glob.glob(p):
            if os.path.isfile(d):
                files.append(d)
            rec_glob("%s/*" % d, files)
    files = []
    rec_glob("%s/*" % mydir, files)
    return [(f, f, 'DATA') for f in files if f not in exclude]

###########################################
import platform
import os
if platform.system() == "Windows":
    a = Analysis(['multibootusb'],
                 pathex=['C:\\Users\\Sundar\\Documents\\multibootusb'],
                 hiddenimports=[],
                 hookspath=None,
                 runtime_hooks=None)

    a.datas += extra_datas('tools', [os.path.join(os.getcwd(),  "tools",  "7zip", "linux", "7z"),
                                    "tools/7zip/linux/7z.so",
                                    "tools/7zip/windows/ptime.exe",
                                    "tools/syslinux/bin/syslinux",
                                    "tools/syslinux/bin/syslinux3",
                                    "tools/syslinux/bin/syslinux4",
                                    "tools/syslinux/bin/syslinux5",
                                    "tools/syslinux/bin/syslinux6"])

else:
    a = Analysis(['./multibootusb'],
             pathex=['/home/sundar/multibootusb'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

    a.datas += extra_datas('tools')

"""
# Add the name of libraries/ dll/ binaries which are not required to be included.
    a.binaries = a.binaries - TOC([
                                 ('libfontconfig.so.1', '', ''),
                                 ('libgthread-2.0.so.0', '', ''),
                                 ('libaudio.so.2', '', ''),
                                 ('libglib-2.0.so.0', '', ''),
                                 ('libpng12.so.0', '', ''),
                                 ('libQt3Support.so.4', '', ''),
                                 ('libbz2.so.1.0', '', ''),
                                 ('libz.so.1', '', ''),
                                 ('libgobject-2.0.so.0', '', ''),
                                 ('libSM.so.6', '', ''),
                                 ('libICE.so.6', '', ''),
                                 ('libXrender.so.1', '', ''),
                                 ('libXext.so.6', '', ''),
                                 ('libX11.so.6', '', ''),
                                 ('libgcc_s.so.1', '', ''),
                                 ('libm.so.6', '', ''),
                                 ('libdl.so.2', '', ''),
                                 ('librt.so.1', '', ''),
                                 ('libGL.so.1', '', ''),
                                 ('libX11.so.6', '', ''),
                                 ('libpthread.so.0', '', ''),
                                 ('libQtSql.so.4', '', ''),
                                 ('libQtXml.so.4', '', ''),
                                 ('libfreetype.so.6', '', '')])
"""

pyz = PYZ(a.pure)

if platform.system() == "Windows":
    #icon='myicon.ico'
    exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='multibootusb-' + version + '.exe',
          #name='multibootusb.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon=os.path.join("tools",  "multibootusb.ico"), manifest='multibootusb.exe.manifest')

else:
    exe = EXE(pyz,
              a.scripts,
              exclude_binaries=True,
              name='multibootusb',
              debug=False,
              strip=None,
              upx=True,
              console=False )

    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=None,
                   upx=True,
                   name='multibootusb')

