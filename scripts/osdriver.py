import os
import platform
import subprocess

from .gen import get_physical_disk_number, log, resource_path

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
    
class Linux(Base):

    def __init__(self):
        self.dd_exe = 'dd'

    def dd_add_args(self, cmd_vec, input, output, bs, count):
        cmd_vec.append('conv=notrunc')

    def physical_disk(self, usb_disk):
        return usb_disk.rstrip('0123456789')

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
        ]:
    globals()[func_name] = getattr(osdriver, func_name)
 
