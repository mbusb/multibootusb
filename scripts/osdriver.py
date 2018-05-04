import logging
import logging.handlers
import os
import platform
import subprocess
import sys


def log(message, info=True, error=False, debug=False, _print=True):
    """
    Dirty function to log messages to file and also print on screen.
    :param message:
    :param info:
    :param error:
    :param debug:
    :return:
    """
    if _print is True:
        print(message)

    # remove ANSI color codes from logs
    # message_clean = re.compile(r'\x1b[^m]*m').sub('', message)

    if info is True:
        logging.info(message)
    elif error is not False:
        logging.error(message)
    elif debug is not False:
        logging.debug(message)

def resource_path(relativePath):
    """
    Function to detect the correct path of file when working with sourcecode/install or binary.
    :param relativePath: Path to file/data.
    :return: Modified path to file/data.
    """
    # This is not strictly needed because Windows recognize '/'
    # as a path separator but we follow the discipline here.
    relativePath = relativePath.replace('/', os.sep)
    for dir_ in [
            os.path.abspath('.'),
            os.path.abspath('..'),
            getattr(sys, '_MEIPASS', None),
            os.path.dirname(os.path.dirname( # go up two levels
                os.path.realpath(__file__))),
            '/usr/share/multibootusb'.replace('/', os.sep),
            ]:
        if dir_ is None:
            continue
        fullpath = os.path.join(dir_, relativePath)
        if os.path.exists(fullpath):
            return fullpath
    log("Could not find resource '%s'." % relativePath)

def get_physical_disk_number(usb_disk):
    """
    Get the physical disk number as detected ny Windows.
    :param usb_disk: USB disk (Like F:)
    :return: Disk number.
    """
    partition, logical_disk = wmi_get_drive_info(usb_disk)
    log("Physical Device Number is %d" % partition.DiskIndex)
    return partition.DiskIndex

def wmi_get_drive_info(usb_disk):
    assert platform.system() == 'Windows'
    import wmi
    c = wmi.WMI()
    for partition in c.Win32_DiskPartition():
        logical_disks = partition.associators("Win32_LogicalDiskToPartition")
        # Here, 'disk' is a windows logical drive rather than a physical drive
        for disk in logical_disks:
            if disk.Caption == usb_disk:
                return (partition, disk)
    raise RuntimeError('Failed to obtain drive information ' + usb_disk)



class Base:

    def run_dd(self, input, output, bs, count):
        cmd = [self.dd_exe, 'if='+input, 'of='+output,
               'bs=%d' % bs, 'count=%d'%count]
        self.dd_add_args(cmd, input, output, bs, count)
        if subprocess.call(cmd) != 0:
            log('Failed to execute [%s]' % str(cmd))
        else:
            log("%s succeeded." % str(cmd))

class Windows(Base):

    def __init__(self):
        self.dd_exe = resource_path('data/tools/dd/dd.exe')

    def dd_add_args(self, cmd_vec, input, output, bs, count):
        pass

    def physical_disk(self, usb_disk):
        return r'\\.\physicaldrive%d' % get_physical_disk_number(usb_disk)

    def mbusb_log_file(self):
        return os.path.join(os.getcwd(), 'multibootusb.log')

class Linux(Base):

    def __init__(self):
        self.dd_exe = 'dd'

    def dd_add_args(self, cmd_vec, input, output, bs, count):
        cmd_vec.append('conv=notrunc')

    def physical_disk(self, usb_disk):
        return usb_disk.rstrip('0123456789')

    def mbusb_log_file(self):
        return '/var/log/multibootusb.log'


driverClass = {
    'Windows' : Windows,
    'Linux'   : Linux,
}.get(platform.system(), None)
if driverClass is None:
    raise Exception('Platform [%s] is not supported.' % platform.system())
osdriver = driverClass()

for func_name in [
        'run_dd',
        'physical_disk',
        'mbusb_log_file',
        ]:
    globals()[func_name] = getattr(osdriver, func_name)


logging.root.setLevel(logging.DEBUG)
fmt = '%(asctime)s.%(msecs)03d %(name)s %(levelname)s %(message)s'
datefmt = '%H:%M:%S'
the_handler = logging.handlers.RotatingFileHandler(
    osdriver.mbusb_log_file(), 'a', 1024*1024, 5)
the_handler.setFormatter(logging.Formatter(fmt, datefmt))
logging.root.addHandler(the_handler)
