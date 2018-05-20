import logging
import logging.handlers
import os
import platform
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from . import udisks

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
    import pythoncom
    pythoncom.CoInitialize()
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


def wmi_get_drive_info_ex(usb_disk):
    assert platform.system() == 'Windows'
    partition, disk = wmi_get_drive_info(usb_disk)
    #print (disk.Caption, partition.StartingOffset, partition.DiskIndex,
    #       disk.FileSystem, disk.VolumeName)

    # Extract Volume serial number off of the boot sector because 
    # retrieval via COM object 'Scripting.FileSystemObject' or wmi interface
    # truncates NTFS serial number to 32 bits.
    with open('//./Physicaldrive%d'%partition.DiskIndex, 'rb') as f:
        f.seek(int(partition.StartingOffset))
        bs_ = f.read(512)
        serial_extractor = {
            'NTFS'  : lambda bs: \
            ''.join('%02X' % c for c in reversed(bs[0x48:0x48+8])),
            'FAT32' : lambda bs: \
            '%02X%02X-%02X%02X' % tuple(
                map(int,reversed(bs[67:71])))
            }.get(disk.FileSystem, lambda bs: None)
        uuid = serial_extractor(bs_)
    mount_point = usb_disk + '\\'
    size_total, size_used, size_free \
        = shutil.disk_usage(mount_point)[:3]
    r = {
        'uuid' : uuid,
        'file_system' : disk.FileSystem,
        'label' : disk.VolumeName.strip() or 'No_label',
        'mount_point' : mount_point,
        'size_total' : size_total,
        'size_used'  : size_used,
        'size_free'  : size_free,
        'vendor'     : 'Not_Found',
        'model'      : 'Not_Found',
        'devtype'    : {
            0 : 'Unknown',
            1 : 'Fixed Disk',
            2 : 'Removable Disk',
            3 : 'Local Disk',
            4 : 'Network Drive',
            5 : 'Compact Disc',
            6 : 'RAM Disk',
        }.get(disk.DriveType, 'DiskType(%d)' % disk.DriveType),
        'disk_index' : partition.DiskIndex,
    }
    # print (r)
    return r


def dd_win_clean_usb(usb_disk_no, status_update):
  """

  """
  host_dir = multibootusb_host_dir()
  temp_file = os.path.join(host_dir, "preference", "disk_part.txt")
  diskpart_text_feed = 'select disk ' + str(usb_disk_no) + '\nclean\nexit'
  with open(temp_file, 'wb') as fp:
      fp.write(bytes(diskpart_text_feed, 'utf-8'))
  status_update('Cleaning the disk...')
  if subprocess.call('diskpart.exe -s ' + temp_file ) == 0:
      for i in range(40):
          # Wait for the drive to reappear if it has ever gone away.
          time.sleep(0.25)
          with open('\\\\.\\PhysicalDrive%d' % usb_disk_no, 'rb'):
              return
      raise RuntimeError('PhysicalDrive%d is now gone!' % usb_disk_no)
  raise RuntimeError("Execution of dd(.exe) has failed.")


class Base:

    def run_dd(self, input, output, bs, count):
        cmd = [self.dd_exe, 'if='+input, 'of='+output,
               'bs=%d' % bs, 'count=%d'%count]
        self.dd_add_args(cmd, input, output, bs, count)
        if subprocess.call(cmd) != 0:
            log('Failed to execute [%s]' % str(cmd))
        else:
            log("%s succeeded." % str(cmd))


    def dd_iso_image(self, input_, output, gui_update, status_update):
        in_file_size = os.path.getsize(input_)
        cmd = [self.dd_exe, 'if=' + input_,
               'of=' + self.physical_disk(output), 'bs=1M']
        self.dd_iso_image_add_args(cmd, input_, output)
        kw_args = {
            'stdout' : subprocess.PIPE,
            'stderr' : subprocess.PIPE,
            'shell'  : False,
            }
        self.add_dd_iso_image_popen_args(kw_args)
        self.dd_iso_image_prepare(input, output, status_update)
        log('Executing => ' + str(cmd))
        dd_process = subprocess.Popen(cmd, **kw_args)
        output_q = queue.Queue()
        while dd_process.poll() is None:
            self.dd_iso_image_readoutput(dd_process, gui_update, in_file_size,
                                         output_q)
        output_lines = [output_q.get() for i in range(output_q.qsize())]
        for l in output_lines:
            log('dd: ' + l)
        return self.dd_iso_image_interpret_result(
            dd_process.returncode, output_lines)

class Windows(Base):

    def __init__(self):
        self.dd_exe = resource_path('data/tools/dd/dd.exe')

    def dd_add_args(self, cmd_vec, input, output, bs, count):
        pass

    def dd_iso_image_prepare(self, input, output, status_update):
        return dd_win_clean_usb(get_physical_disk_number(output),
                                status_update)

    def dd_iso_image_add_args(self, cmd_vec, input_, output):
        cmd_vec.append('--progress')

    def add_dd_iso_image_popen_args(self, dd_iso_image_popen_args):
        dd_iso_image_popen_args['universal_newlines'] = True

    def dd_iso_image_readoutput(self, dd_process, gui_update, in_file_size,
                                output_q):
        for line in iter(dd_process.stderr.readline, ''):
            line = line.strip()
            if line:
                l = line.replace(',', '')
                if l[-1:] == 'M':
                    bytes_copied = float(l.rstrip('M')) * 1024 * 1024
                elif l.isdigit():
                    bytes_copied = float(l)
                else:
                    if 15 < output_q.qsize():
                        output_q.get()
                    output_q.put(line)
                    continue
                gui_update(bytes_copied / in_file_size * 100.)
                continue
        # Now the 'dd' process should have completed or going to soon.

    def dd_iso_image_interpret_result(self, returncode, output_list):
        # dd.exe always returns 0
        if any([ 'invalid' in s or 'error' in s for s
                 in [l.lower() for l in output_list] ]):
            return '\n'.join(output_list)
        else:
            return None

    def physical_disk(self, usb_disk):
        return r'\\.\physicaldrive%d' % get_physical_disk_number(usb_disk)

    def mbusb_log_file(self):
        return os.path.join(os.getcwd(), 'multibootusb.log')

    def find_mounted_partitions_on(self, usb_disk):
        return []  # No-op until UnmountedContext() get implemented for Windows

    def multibootusb_host_dir(self):
        return os.path.join(tempfile.gettempdir(), "multibootusb")

    def gpt_device(self, dev_name):
        partition, disk = wmi_get_drive_info(dev_name)
        return  partition.Type.startswith('GPT:')

class Linux(Base):

    def __init__(self):
        self.dd_exe = 'dd'

    def dd_iso_image_prepare(self, input, output, status_update):
        pass

    def dd_add_args(self, cmd_vec, input, output, bs, count):
        cmd_vec.append('conv=notrunc')

    def dd_iso_image_add_args(self, cmd_vec, input_, output):
        cmd_vec.append('oflag=sync')

    def add_dd_iso_image_popen_args(self, dd_iso_image_popen_args):
        pass

    def dd_iso_image_readoutput(self, dd_process, gui_update, in_file_size,
                                output_q):
        # If this time delay is not given, the Popen does not execute
        # the actual command
        time.sleep(0.1)
        dd_process.send_signal(signal.SIGUSR1)
        dd_process.stderr.flush()
        while True:
            time.sleep(0.1)
            out_error = dd_process.stderr.readline().decode()
            if out_error:
                if 'bytes' in out_error:
                    bytes_copied = float(out_error.split(' ', 1)[0])
                    gui_update( bytes_copied / in_file_size * 100. )
                    break
                if 15 < output_q.qsize():
                    output_q.get()
                output_q.put(out_error.rstrip())
            else:
                # stderr is closed
                break

    def dd_iso_image_interpret_result(self, returncode, output_list):
        return None if returncode==0 else '\n'.join(output_list)

    def physical_disk(self, usb_disk):
        return usb_disk.rstrip('0123456789')

    def mbusb_log_file(self):
        return '/var/log/multibootusb.log'

    def find_mounted_partitions_on(self, usb_disk):
        return udisks.find_mounted_partitions_on(usb_disk)

    def multibootusb_host_dir(self):
        return os.path.join(os.path.expanduser('~'), ".multibootusb")

    def gpt_device(self, dev_name):
        disk_dev = dev_name.rstrip('0123456789')
        cmd = ['parted', disk_dev, '-s', 'print']
        with open(os.devnull) as devnull:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, stdin=devnull)
            _cmd_out, _err_out = p.communicate()
            p.wait()
        if p.returncode != 0:
            lang = os.getenv('LANG')
            encoding = lang.rsplit('.')[-1] if lang else 'utf-8'
            raise RuntimeError(str(_err_out, encoding))
        subprocess.check_call(['partprobe', disk_dev])
        if b'msdos' in _cmd_out:
            return False
        if b'gpt' in _cmd_out:
            return True
        raise RuntimeError("Disk '%s' is uninitialized and not usable." %
                           disk_dev)


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
        'dd_iso_image',
        'find_mounted_partitions_on',
        'multibootusb_host_dir',
        'gpt_device',
        ]:
    globals()[func_name] = getattr(osdriver, func_name)

def init_logging():
    logging.root.setLevel(logging.DEBUG)
    fmt = '%(asctime)s.%(msecs)03d %(name)s %(levelname)s %(message)s'
    datefmt = '%H:%M:%S'
    the_handler = logging.handlers.RotatingFileHandler(
        osdriver.mbusb_log_file(), 'a', 1024*1024, 5)
    the_handler.setFormatter(logging.Formatter(fmt, datefmt))
    logging.root.addHandler(the_handler)
