import sys
from unittest.mock import MagicMock, patch, sentinel

sys.path = ['..'] + sys.path
from scripts import distro
from scripts import gen


def test_distro_detection():
    def os_path_exists(f):
        if f.endswith('multibootusb.log'):
            return False
        return True
    os_path_exists_mock = MagicMock()
    log_mock = MagicMock()
    @patch('os.path.exists', os_path_exists)
    @patch('scripts.distro.log', log_mock)
    def _():
        fn = distro.detect_iso_from_file_list
        assert fn('fake.iso', ['BOOT.wim', 'Sources']) == 'Windows'
        assert fn('fake.iso', ['BOOT.wim', 'Sause']) is None
        assert fn('fake.iso', ['config.isoclient', 'foo']) == 'opensuse'
        assert fn('fake.iso', ['bar', 'dban', 'foo']) == 'slitaz'
        assert fn('fake.iso', ['memtest.img']) == 'memtest'
        assert fn('fake.iso', ['mt86.png','isolinux']) == 'raw_iso'
        assert fn('fake.iso', ['menu.lst']) == 'grub4dos'
        assert fn('fake.iso', ['bootwiz.cfg', 'bootmenu_logo.png']) == \
            'grub4dos_iso'
    _()
    log_mock.assert_called_with('Examined 2 filenames in the iso '
                                'but could not determine the distro.')
    
if __name__ == '__main__':
    test_distro_detection()
