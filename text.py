import os
import re
import platform
#from .scripts import gen
#from .scripts import config
#from .scripts import iso


def write_to_file(file_path, _strings):

    try:
        if not os.path.exists(file_path):
            open(file_path, 'a').close()

        with open(file_path, 'a') as f:
            f.write(_strings + '\n')
    except:
        gen.log('Error writing to loopback.cfg file..')


def string_in_file(_file, search_text):
    """

    :param _file:
    :param search_text:
    :return:
    """
    if search_text in open(_file).read().lower():
        return True

isolinux_dir = os.path.join('E:\\', 'DISTROS', 'isolinux')
usb_mount = 'G:\\'
mbusb_dir = os.path.join(usb_mount, 'multibootusb')
isolinux_dir = 'G:\\multibootusb\\dban-2.3.0_i586'
isolinux_dir = 'G:\\multibootusb\\dsl-4.11.rc2\\boot\\isolinux'

def kernel_exist(search_text, match_line):
    kernel_line = ''
    if (search_text + '=') in match_line:
        kernel_path = match_line.replace((search_text + '='), '').strip()
        search_text = search_text.replace('=', '')
    else:
        kernel_path = match_line.replace(search_text, '').strip()

    if os.path.exists(os.path.join(usb_mount, kernel_path)):
        kernel_line = search_text.lower().replace('kernel', 'linux') + ' ' + kernel_path.strip()
    elif os.path.exists(os.path.join(isolinux_dir, kernel_path)):
        kernel_line = search_text.lower().replace('kernel', 'linux') + ' /multibootusb/' + kernel_path.strip()
    elif ',/' in kernel_path:
        kernel_line = search_text.lower().replace('kernel', 'linux') + ' ' + kernel_path.strip()
        kernel_line = kernel_line.replace(',/', ' /')
    elif 'z,' in kernel_path:
        kernel_line = search_text.lower().replace('kernel', 'linux') + ' ' + kernel_path.strip()
        kernel_line = kernel_line.replace('z,', ' /multibootusb')
    else:
        kernel_line = ''

    return kernel_line


def iso2grub2(iso_dir):
    """
    Function to convert syslinux configuration to grub2 accepted configuration format. Features implemented are similar
    to that of grub2  'loopback.cfg'. This 'loopback.cfg' file can be later on caled directly from grub2. The main 
    advantage of this function is to generate the 'loopback.cfg' file automatically without manual involvement. 
    :param iso_dir: Path to distro install directory for looping through '.cfg' files.
    :param file_out: Path to 'loopback.cfg' file. By default it is set to root of distro install directory.
    :return:
    """
    # grub_file_path = os.path.join(config.usb_mount, 'multibootusb', iso.iso_basename(config.image_path), 'loopback.cfg')
    grub_file_path = 'text.txt'
    # Loop though the distro installed directory for finding config files
    for dirpath, dirnames, filenames in os.walk(iso_dir):
        for f in filenames:
            # We will strict to only files ending with '.cfg' extension. This is the file extension isolinux or syslinux
            #  recommends for writing configurations
            if f.endswith((".cfg", ".CFG")):
                cfg_file_path = os.path.join(dirpath, f)
                # We will omit the grub directory
                if 'grub' not in cfg_file_path:
                    # we will use only files containing strings which can be converted to grub2 cfg style
                    if string_in_file(cfg_file_path, 'menu label') or string_in_file(cfg_file_path, 'label'):
                        with open(cfg_file_path, "r", errors='ignore') as cfg_file_str:
                            data = cfg_file_str.read()
                            # Make sure that lines with menu label, kernel and append are available for processing
                            ext_text = re.finditer('(menu label|label)(.*?)(?=(menu label|label))', data, re.I|re.DOTALL)
                            # if (sum(1 for j in ext_text)) == 0:
                            #    ext_text = re.finditer('(menu label|label)(.*?)\Z', data, re.I|re.DOTALL)
                            if ext_text:
                                for m in ext_text:
                                    menuentry = ''
                                    kernel = ''
                                    kernel_line = ''
                                    boot_options = ''
                                    initrd_line = ''
                                    initrd = ''

                                    # Extract line containing 'menu label' and convert to menu entry of grub2
                                    if 'menu label' in m.group().lower():
                                        menu_line = re.search('menu label(.*)\s', m.group(), re.I).group()
                                        menuentry = 'menuentry ' + re.sub(r'menu label', '', menu_line, re.I, ).strip()
                                        # Ensure that we do not have caps menu label in the menuentry
                                        menuentry = menuentry.replace('MENU LABEL', '')
                                    elif 'label ' in m.group().lower():
                                        # Probably config does not use 'menu label' line. Just line containing 'label'
                                        #  and convert to menu entry of grub2
                                        menu_line = re.search('^label(.*)\s', m.group(), re.I).group()
                                        menuentry = 'menuentry ' + re.sub(r'label', '', menu_line, re.I, ).strip()
                                        # Ensure that we do not have caps label in the menuentry
                                        menuentry = menuentry.replace('LABEL', '')
                                        #print(menuentry)

                                    # Extract kernel line and change to linux line of grub2
                                    if 'kernel' in m.group().lower() or 'linux' in m.group().lower():
                                        # print(m.group())
                                        kernel_text = re.findall('((kernel|linux)[= ].*?[ \s])', m.group(), re.I)
                                        match_count = len(re.findall('((kernel|linux)[= ].*?[ \s])', m.group(), re.I))
                                        if match_count is 1:
                                            kernel_line = kernel_exist(kernel_text[0][1], kernel_text[0][0])
                                        elif match_count > 2:
                                            for _lines in kernel_text:
                                                if kernel_line is '':
                                                    continue
                                                else:
                                                    kernel_line = kernel_exist(kernel_text[0][1], _lines[0][0])
                                                    break

                                    if 'initrd' in m.group().lower():
                                        initrd_text = re.findall('((initrd)[= ].*?[ \s])', m.group(), re.I)
                                        match_count = len(re.findall('((initrd)[= ].*?[ \s])', m.group(), re.I))
                                        if match_count is 1:
                                            initrd_line = kernel_exist(initrd_text[0][1], initrd_text[0][0])
                                        elif match_count > 2:
                                            for _lines in initrd_text:
                                                if kernel_line is '':
                                                    continue
                                                else:
                                                    initrd_line = kernel_exist(initrd_text[0][1], _lines[0][0])
                                                    break

                                    if 'append' in m.group().lower():
                                        append_line = re.search('append (.*)\s', m.group(), re.I).group()
                                        boot_options = re.sub(r'((initrd[= ])(.*?)[ ])', '', append_line, re.I, flags=re.DOTALL)
                                        boot_options = re.sub(r'append', '', boot_options, re.I).strip()
                                        boot_options = boot_options.replace('APPEND', '')

                                    if kernel_line.strip():
                                        linux = kernel_line.strip() + ' ' + boot_options.strip().strip()
                                    else:
                                        linux = ''

                                    if menuentry.strip() and linux.strip() and initrd_line.strip():
                                        print('\n', menuentry)
                                        print(linux)
                                        print(initrd_line, '\n')
                                        '''
                                        write_to_file(grub_file_path, menuentry + '{')
                                        write_to_file(grub_file_path, '    ' + linux)
                                        write_to_file(grub_file_path, '    ' + initrd)
                                        write_to_file(grub_file_path, '}\n')
                                        '''
                                    elif menuentry.strip() and linux.strip():
                                        print('\n', menuentry)
                                        print(linux, '\n')
                                        '''
                                        write_to_file(grub_file_path, menuentry + '{')
                                        write_to_file(grub_file_path, '    ' + linux)
                                        write_to_file(grub_file_path, '}\n')
                                        '''



                                    '''
                                    elif 'linux' in m.group().lower():
                                        # print(m.group())
                                        # kernel_line = re.findall('((linux)[= ].*?[ \s])', m.group(), re.I)
                                        # match_count = len(re.findall('((linux)[= ].*?[ \s])', m.group(), re.I))
                                        # print(match_count)
                                        kernel_text = re.findall('((linux)[= ].*?[ \s])', m.group(), re.I)
                                        # print(kernel_text[0][1])
                                        match_count = len(re.findall('((linux)[= ].*?[ \s])', m.group(), re.I))
                                        if match_count is 1:
                                            print('linux  +++++++++++++++++++++++++++')
                                            kernel_line = kernel_exist(kernel_text[0][1], kernel_text[0][0])
                                            if kernel_line is not False:
                                                print('kernel_line is::', kernel_line)
                                        elif match_count > 1:
                                            print('+++++++++++++++++++++++++++ linux')
                                            for _lines in kernel_text:
                                                #print(_lines[0])
                                                kernel_line = kernel_exist(kernel_text[0][1], _lines[0])
                                                if kernel_line is False:
                                                    continue
                                                else:
                                                    print('kernel_line is::', kernel_line)
                                                    break
                                    
                                        if match_count is 1:
                                            print('------------------------')
                                            print(kernel_exist(kernel_line[0][0]))
                                        elif match_count > 2:
                                            for _lines in kernel_line:
                                                print(kernel_exist(_lines))
                                        #print(kernel_line)
                                        
                                        or 'linux ' in m.group().lower():
                                        kernel_line = re.findall('((kernel|linux)[= ].*?[ \s])', m.group(), re.I)[0][0]

                                        kernel = kernel_line.strip().replace('kernel', 'linux')
                                        kernel = kernel.strip().replace('KERNEL', 'linux')
                                        if 'linux=/multibootusb' in kernel.lower():
                                            kernel = kernel.strip().replace('linux=', 'linux ')

                                        elif 'linux=' in kernel.lower():
                                            kernel = kernel.strip().replace('linux=', 'linux /multibootusb/' +
                                                                                    iso.iso_basename(config.image_path) + '/'
                                                                                    + iso.isolinux_bin_dir(config.image_path).replace('\\', '/') + '/')
                                        elif 'linux /' not in kernel:
                                            kernel = kernel.strip().replace('linux ', 'linux /multibootusb/' +
                                                                                    iso.iso_basename(config.image_path) + '/'
                                                                                    + iso.isolinux_bin_dir(config.image_path).replace('\\', '/') + '/')

                                        # Ensure that we do not have linux parameter in caps
                                        kernel = kernel.replace('LINUX ', 'linux ')
                                        kernel = kernel.replace('Linux ', 'linux ')
                                        # Fix for solus os. Patch welcome.
                                        if config.distro == 'fedora' and '/linux' in kernel:
                                            kernel = kernel.replace('/linux', '/kernel')

                                    # Ensure that initrd is present in the config file
                                    if 'initrd' in m.group().lower():
                                        # Extract only initrd line which starts in first in the line
                                        if re.search('^initrd', m.group(), re.I|re.MULTILINE):
                                            initrd = re.findall('(initrd[= ].*?[ \s])', m.group(), re.I)[0]
                                            if not initrd:
                                                # print('initrd not in seperate line')
                                                initrd = re.findall('(initrd[= ].*[ \s])', initrd, re.I|re.DOTALL)[0]
                                                # Ensure that multiple initrd of syslinux are converted to grub2
                                                # standard
                                                initrd = initrd.replace(',/', ' /')
                                                initrd = initrd.replace('z,', 'z /multibootusb/' +
                                                                        iso.iso_basename(config.image_path) + '/'
                                                                        + iso.isolinux_bin_dir(config.image_path).replace('\\', '/')  + '/')
                                                #print('initrd')
                                        else:
                                            # Extract initrd parameter from within the line
                                            initrd = re.findall('(initrd[= ].*?[ ])', m.group(), re.I|re.DOTALL)[0]
                                            initrd = initrd.replace(',/', ' /')
                                            initrd = initrd.replace('z,', 'z /multibootusb/' +
                                                                    iso.iso_basename(config.image_path) + '/'
                                                                    + iso.isolinux_bin_dir(config.image_path).replace('\\', '/')  + '/')
                                            #print(initrd)

                                        # Ensure that we change the relative path to absolute path
                                        if 'initrd=/multibootusb' in initrd.lower():
                                            initrd = initrd.strip().replace('initrd=', 'initrd ')
                                            initrd = initrd.strip().replace('INITRD=', 'initrd ')

                                        elif 'initrd=' in initrd.lower():
                                            initrd = initrd.strip().replace('initrd=', 'initrd /multibootusb/' +
                                                                          iso.iso_basename(config.image_path) + '/'
                                                                          + iso.isolinux_bin_dir(config.image_path).replace('\\', '/') + '/')

                                        # Ensure that there is no caps which is not accepted by grub2
                                        initrd = initrd.replace('INITRD', 'initrd')

                                    # Extract append line for getting boot options
                                    if 'append' in m.group().lower():
                                        append = re.search('append (.*)\s', m.group(), re.I).group()
                                        boot_options = re.sub(r'((initrd[= ])(.*?)[ ])', '', append, re.I, flags=re.DOTALL)

                                        # Ensure that there is no append line exisit
                                        boot_options = re.sub(r'append', '', boot_options, re.I).strip()
                                        boot_options = boot_options.replace('APPEND', '')

                                    # We will ensure that all options are met as per grub2 specifications and
                                    # write to file
                                    linux = kernel.strip() + ' ' + boot_options.strip().strip()
                                    if menuentry and linux and initrd:
                                        # print('\n', menuentry)
                                        # print(linux)
                                        # print(initrd)
                                        write_to_file(grub_file_path, menuentry + '{')
                                        write_to_file(grub_file_path, '    ' + linux)
                                        write_to_file(grub_file_path, '    ' + initrd)
                                        write_to_file(grub_file_path, '}\n')
                                    elif menuentry and linux.strip():
                                        write_to_file(grub_file_path, menuentry + '{')
                                        write_to_file(grub_file_path, '    ' + linux)
                                        write_to_file(grub_file_path, '}\n')
                            '''

if __name__ == '__main__':
    if platform.system() == 'Windows':
        iso_dir = os.path.join('E:\\', 'DISTROS')
        #iso_dir = 'G:\\multibootusb\\slitaz-rolling-core64'
        iso_dir = 'G:\\multibootusb\\slitaz-4.0'
        #iso_dir = 'G:\\multibootusb\\dban-2.3.0_i586'
        #iso_dir = 'G:\\multibootusb\\G_DATA_BootCD\\boot\\isolinux'
        #iso_dir = 'G:\\multibootusb\\manjaro-kde-16.10.3-stable-x86_64'
        #iso_dir = 'G:\multibootusb\debian-live-8.3.0-amd64-lxde-desktop\isolinux'
        #iso_dir = 'G:\\multibootusb\\dban-2.3.0_i586'
        #iso_dir = 'G:\\multibootusb\\cd140201'
        #iso_dir = 'G:\\multibootusb\\debian-live-8.3.0-amd64-lxde-desktop'
        #iso_dir = 'G:\\multibootusb\\Hiren_BootCD\\HBCD'
        #iso_dir = 'G:\\multibootusb\\ubuntu-14.04.2-desktop-amd64'
        #iso_dir = 'G:\\multibootusb\\kav_rescue_10'
        iso_dir = 'G:\\multibootusb\\dban-2.3.0_i586'
        iso_dir = 'G:\\multibootusb\\dsl-4.11.rc2'
    else:
        iso_dir = '/media/sundar/Fun/DISTROS'

    lines = iso2grub2(iso_dir)