from functools import reduce
import os
import sys
from unittest.mock import MagicMock, patch, sentinel

sys.path = ['..'] + sys.path
from scripts import config
from scripts import gen
from scripts import grub
from scripts import iso

class OpenMock:
    def __init__(self, *args, **kw):
        self.writes = []

    def read(self):
        return """LABEL core
	MENU LABEL SliTaz core Live
	COM32 c32box.c32
	append linux /boot/bzImage initrd=/boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz rw root=/dev/null video=-32 autologin
"""
    def write(self, data):
        self.writes.append(data)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

OPEN_MOCK = OpenMock()

def gen_log(obj):
    print ('[*] %s' % obj)

def my_open(fname, mode, **kw):
    return OPEN_MOCK

def iso_bin_dir(iso_image):
    return 'isolinux'

def os_path_exists(f):
    chunks = reduce(lambda accum, x : accum + x.split('/'), f.split('\\'), [])
    if chunks[-1] in ['multibootusb.log', 'loopback.cfg']:
        return True
    if 'arch' in chunks:
        return True
    if chunks[1] in ['rootfs1.gz', 'rootfs2.gz']:
        return True
    if chunks == ['multibootusb', 'debian-sid', 'boot', 'rootfs4.gz']:
        return True
    return False

def os_walk(dirpath):
    return [('isolinux', [], ['isolinux.cfg'])]

def test_iso2grub2():

    gen_log_mock = MagicMock()
    iso_bin_dir_mock = MagicMock()
    os_walk_mock = MagicMock()
    os_path_exists_mock = MagicMock()
    open_mock = MagicMock()
    @patch('scripts.gen.log', gen_log_mock)
    @patch('scripts.iso.isolinux_bin_dir', iso_bin_dir_mock)
    @patch('os.walk', os_walk)
    @patch('os.path.exists', os_path_exists)
    @patch('builtins.open', open_mock)
    def _():
        gen_log_mock.side_effect = gen_log
        open_mock.side_effect = my_open
        os_path_exists_mock.side_effect = os_path_exists
        os_walk_mock.side_effect = os_walk
        iso_bin_dir_mock.side_effect = iso_bin_dir

        config.image_path = '/home/suzuki/Downloads/debian-sid.iso'
        grub.iso2grub2('/tmp/mbusb/debian', 'loopback.cfg')
    _()
    assert ''.join(OPEN_MOCK.writes)=="""# Extracted from isolinux/isolinux.cfg
menuentry "SliTaz core Live" {
    linux /multibootusb/debian-sid/arch/boot/bzImage rw root=/dev/null video=-32 autologin
    initrd /multibootusb/debian-sid/boot/rootfs4.gz /multibootusb/debian-sid/arch/boot/rootfs3.gz /boot/rootfs2.gz /boot/rootfs1.gz
}

"""
    print ("Test Passed.")

test_iso2grub2()
