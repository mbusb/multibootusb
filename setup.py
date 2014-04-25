from distutils.core import setup
import os
import sys
mbusb_version = open(os.path.join("tools", "version.txt"), 'r').read().strip()
setup(
    name='multibootusb',
    version=mbusb_version,
    packages=['scripts', 'pyudev'],
    scripts = ['multibootusb'],
    platforms = ['Linux'],
    url='http://multibootusb.org/',
    license='General Public License (GPL)',
    author='Sundar',
    author_email='feedback.multibootusb@gmail.com',
    description='Create multi boot live Linux on a USB disk...',
    long_description = 'The multibootusb is an advanced cross-platform application for installing/uninstalling Linux operating systems on to USB flash drives.',
    data_files = [("/usr/share/applications",["data/multibootusb.desktop"]),
                  ('/usr/share/pixmaps',["data/multibootusb.png"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools"),["tools/checking.gif"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools"),["tools/mbr.bin"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools"),["tools/version.txt"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools"),["tools/multibootusb.png"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools", "multibootusb"),["tools/multibootusb/chain.c32"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools", "multibootusb"),["tools/multibootusb/extlinux.cfg"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools", "multibootusb"),["tools/multibootusb/grub.exe"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools", "multibootusb"),["tools/multibootusb/memdisk"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools", "multibootusb"),["tools/multibootusb/menu.c32"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools", "multibootusb"),["tools/multibootusb/menu.lst"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools", "multibootusb"),["tools/multibootusb/syslinux.cfg"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools", "multibootusb"),["tools/multibootusb/vesamenu.c32"]),
                  (os.path.join(sys.prefix,"multibootusb", "tools"),["tools/syslinux.zip"])]
)