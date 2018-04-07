import sys
import unittest
from unittest.mock import MagicMock as MM, patch, mock_open

sys.path = ['..'] + sys.path
from scripts import distro
from scripts import gen

class DistoDetection(unittest.TestCase):

    def distro(self, isobin_exists, filelist_in_iso, input_text):
        mock_isobin_exists = MM(return_value=isobin_exists)
        mock_iso_list = MM(return_value=filelist_in_iso)
        mock_os_walk = MM(return_value=[('/', [], ['grub.cfg'])])
        @patch('scripts.distro.isolinux_bin_exist', mock_isobin_exists)
        @patch('os.walk', mock_os_walk)
        @patch('scripts._7zip.list_iso', mock_iso_list)
        @patch('builtins.open', mock_open(read_data=input_text))
        def test_when_isolinux_bin_is_available():
            return (distro.distro('{iso-cfg-dir}', 'ProDOS2.iso'))
        return test_when_isolinux_bin_is_available()



    def test_filebased_detection(self):
        test_inputs = [
            ('f4ubcd',         '',                 ['f4ubcd']),
            ('memdisk_iso',    '',                 []),
            ('memdisk_iso',    'debian-installer', ['casper']),
            ('debian-install', 'debian-installer', []),
            ('alpine',         '',                 ['alpine-release']),
            ('memdisk_iso',    '',                 ['']),
            ]
        for expected_distro, input_texts, file_list in test_inputs:
            for input_text in input_texts.split('|'):
                distro = self.distro(True, file_list, input_text)
                assert distro==expected_distro, (
                    "From \"%s&%s\", '%s' is expected but got '%s'" %
                    (input_text, file_list, expected_distro, distro))


    def test_detection_with_isobin(self):
        test_inputs = [
            ('parted-magic', 'pmagic|partedmagic',       True),
            ('memdisk_iso',  'pmagic|partedmagic',       False),
            ('debian',       'boot=live',                True),
            ('memdisk_iso',  'boot=live',                False),
            ('sms',          'sms.jpg|vector |autoexec', True),
            ('memdisk_iso',  'sms.jpg|vector |autoexec', False),
            ]
        for expected_distro, input_texts, isobin_exists in test_inputs:
            for input_text in input_texts.split('|'):
                distro = self.distro(isobin_exists, [], input_text)
                assert distro==expected_distro, (
                    "From \"%s&isobin=%s\", '%s' is expected but got '%s'" %
                    (input_text, isobin_exists, expected_distro, distro))


    def test_detection_isobin_agnostic(self):
        test_inputs = [
            ('ubcd',            'ubcd'),
            ('sgrubd2',         'Super Grub Disk'),
            ('hbcd',            'hbcd'),
            ('systemrescuecd',  'systemrescuecd'),
            ('mageialive',      'mgalive'),
            ('arch',            'archisolabel|misolabel|parabolaisolabel'),
            ('chakra',          'chakraisolabel'),
            ('kaos',            'kdeosisolabel'),
            ('memdisk_iso',     'grml'),
            ('grml',            'grml live-media-path=/dev/sda1'),
            ('debian-install',  'debian-installer'),
            ('solydx',          'solydx'),
            ('knoppix',         'knoppix'),
            ('fedora',          'root=live:CDLABEL=|redcore'),
            ('redhat',          'redhat'),
            ('slitaz',          'slitaz|dban |ophcrack|tinycore'
             '|rescue.cpi|xpud|untangle|4mlinux|partition wizard'
             '|android-x86.png|riplinux|lebel dummy'
             '|http://pogostick.net/~pnh/ntpasswd/|AVG Rescue CD'
             '|AntivirusLiveCD|lkrn|Nanolinux|OSForensics'
             '|minimal Slackware|Slackware-HOWTO'),
            ('opensuse-install', 'class opensuse'),
            ('ubuntu',           'boot=casper'),
            ('wifislax',         'wifislax'),
            ('slax',             'slax'),
            ('antix',            'antix'),
            ('porteus',          'porteus'),
            ('pclinuxos',        'livecd=livecd|PCLinuxOS'),
            ('gentoo',           'looptype=squashfs|http://dee.su/liberte'),
            ('finnix',           'finnix'),
            ('wifiway',          'wifiway'),
            ('puppy',            'puppy|quirky|fatdog|slacko|xenialpup'),
            ('ipcop',            'ipcop'),
            ('ipfire',           'ipfire'),
            ('zenwalk',          'zenwalk|slack|salix'),
            ('salix-live',       'zenwalk live|live slack|live salix'),
            ('zenwalk',          'zenwalk|slack|salix'),
            ('puppy',            'zenwalk slacko|slacko slack'),
            ('ubuntu-server',    'ubuntu server'),
            ('centos',           'root=live:CDLABEL=CentOS'),
            ('centos-install',   'Install CentOS'),
            ('centos',           'CentOS'),
            ('trinity-rescue',   'Trinity Rescue Kit'),
            ('kaspersky',        'http://support.kaspersky.com'),
            ('alt-linux',        'ALT Linux'),
            ('Windows',          'Sergei Strelec'),
            ('ReactOS',          'ReactOS'),
            ('fsecure',          'fsecure'),
            ('pc-unlocker',      'default rwp'),
            ('pc-tool',          '/system/stage1'),
            ('grub2only',        'vba32rescue'),
            ('rising-av',        'BOOT_IMAGE=rising'),
            ('Avira-RS',         'Avira Rescue System'),
            ('insert',           'BOOT_IMAGE=insert'),
            ]

        for expected_distro, input_texts in test_inputs:
            for input_text in input_texts.split('|'):
                distro = self.distro(False, [], input_text)
                assert distro==expected_distro, (
                    "From \"%s\", '%s' is expected but got '%s'" %
                    (input_text, expected_distro, distro))


    def test_distro_detection(self):
        def os_path_exists(f):
            if f.endswith('multibootusb.log'):
                return False
            return True
        os_path_exists_mock = MM()
        log_mock = MM()
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
    unittest.main()
