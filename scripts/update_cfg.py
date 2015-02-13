import shutil
import gen_fun
import os
import re
import usb
import config


def update_distro_cfg_files(distro, usb_disk, iso_name, iso_cfg_ext_dir, persistence_size, iso_link):
    print "Updating distro config files..."
    usb_details = usb.usb_details(usb_disk)
    usb_label = usb_details['label']
    usb_uuid = usb_details['uuid']
    usb_mount_path = usb_details['mount']
    for dirpath, dirnames, filenames in os.walk(iso_cfg_ext_dir):
        for f in filenames:
            if f.endswith(".cfg"):
                cfg_file = os.path.join(dirpath, f)
                try:
                    string = open(cfg_file).read()
                except IOError:
                    print "Unable to read " + cfg_file
                else:
                    replace_text = r'\1/multibootusb/' + os.path.splitext(iso_name)[0] + '/'
                string = re.sub(r'([ \t =,])/', replace_text, string)
                if distro == "ubuntu":
                    string = re.sub(r'boot=casper',
                                    'boot=casper cdrom-detect/try-usb=true floppy.allowed_drive_mask=0 ignore_uuid ignore_bootid root=UUID=' + str(
                                        usb_uuid) + ' live-media-path=/multibootusb/' +
                                    os.path.splitext(iso_name)[0] + '/casper', string)
                    if not persistence_size == 0:
                        string = re.sub(r'boot=casper', 'boot=casper persistent persistent-path=/multibootusb/' +
                                        os.path.splitext(iso_name)[0] + "/", string)
                elif distro == "debian":
                    string = re.sub(r'boot=live', 'boot=live ignore_bootid live-media-path=/multibootusb/' +
                                    os.path.splitext(iso_name)[0] + '/live', string)
                    if not persistence_size == 0:
                        string = re.sub(r'boot=live', 'boot=live persistent persistent-path=/multibootusb/' +
                                                  os.path.splitext(iso_name)[0] + "/", string)

                elif distro == "ubuntu-server":
                    string = re.sub(r'file', 'cdrom-detect/try-usb=true floppy.allowed_drive_mask=0 ignore_uuid ignore_bootid root=UUID=' + str(
                                        usb_uuid + ' file'), string)
                elif distro == "fedora":
                    string = re.sub(r'root=\S*', 'root=UUID=' + str(usb_uuid), string)
                    if re.search(r'liveimg', string, re.I):
                        string = re.sub(r'liveimg', 'liveimg live_dir=/multibootusb/' +
                                                 os.path.splitext(iso_name)[0] + '/LiveOS', string)
                    elif re.search(r'rd.live.image', string, re.I):
                        string = re.sub(r'rd.live.image', 'rd.live.image rd.live.dir=/multibootusb/' +
                                                 os.path.splitext(iso_name)[0] + '/LiveOS', string)
                    if not persistence_size == 0:
                        if re.search(r'liveimg', string, re.I):
                            string = re.sub(r'liveimg', 'liveimg overlay=UUID=' + usb_uuid, string)
                        elif re.search(r'rd.live.image', string, re.I):
                            string = re.sub(r'rd.live.image', 'rd.live.image rd.live.overlay=UUID=' + usb_uuid, string)
                        string = re.sub(r' ro ', ' rw ', string)
                elif distro == "parted-magic":
                    string = re.sub(r'initrd=',
                                    'directory=/multibootusb/' + os.path.splitext(iso_name)[0] + '/ initrd=',
                                    string)
                elif distro == "ubcd":
                    string = re.sub(r'iso_filename=\S*', 'directory=/multibootusb/' + os.path.splitext(iso_name)[0],
                                    string, flags=re.I)
                elif distro == "ipcop":
                    string = re.sub(r'ipcopboot=cdrom\S*', 'ipcopboot=usb', string)
                elif distro == "puppy":
                    string = re.sub(r'pmedia=cd\S*',
                                    'pmedia=usbflash psubok=TRUE psubdir=/multibootusb/' + os.path.splitext(iso_name)[0] + '/',
                                    string)
                elif distro == "slax":
                    string = re.sub(r'initrd=', r'from=/multibootusb/' + os.path.splitext(iso_name)[
                        0] + '/slax fromusb initrd=', string)
                elif distro == "knoppix":
                    string = re.sub(r'(append)',
                                    r'\1  knoppix_dir=/multibootusb/' + os.path.splitext(iso_name)[0] + '/KNOPPIX',
                                    string)
                elif distro == "gentoo":
                    string = re.sub(r'append ', 'append real_root=' + usb_disk + ' slowusb subdir=/multibootusb/' +
                                    os.path.splitext(iso_name)[0] + '/ ', string, flags=re.I)
                elif distro == "systemrescuecd":
                    rows = []
                    subdir = '/multibootusb/' + os.path.splitext(iso_name)[0] + '/'
                    for line in string.splitlines(True):
                        addline = True
                        if re.match(r'append.*--.*', line, flags=re.I):
                            line = re.sub(r'(append)(.*)--(.*)', r'\1\2subdir=' + subdir + r' --\3 subdir=' + subdir,
                                   line, flags=re.I)
                        elif re.match(r'append', line, flags=re.I):
                                line = re.sub(r'(append)', r'\1 subdir=' + subdir, line, flags=re.I)
                        elif re.match(r'label rescue(32|64)_1', line, flags=re.I):
                            rows.append(line)
                            rows.append('append subdir=%s\n' % (subdir,))
                            addline = False

                        if addline:
                            rows.append(line)

                    string = ''.join(rows)
                elif distro == "arch" or distro == "chakra":
                    string = re.sub(r'isolabel=\S*', 'isodevice=/dev/disk/by-uuid/' + str(usb_uuid), string,
                                    flags=re.I)
                    string = re.sub(r'isobasedir=',
                                    'isobasedir=/multibootusb/' + os.path.splitext(iso_name)[0] + '/', string,
                                    flags=re.I)
                elif distro == "suse" or distro == "opensuse":
                    if re.search(r'opensuse_12', string, re.I):
                        string = re.sub(r'append', 'append loader=syslinux isofrom_system=/dev/disk/by-uuid/' + str(
                            usb_uuid) + ":/" + str(iso_name), string, flags=re.I)
                    else:
                        string = re.sub(r'append', 'append loader=syslinux isofrom_device=/dev/disk/by-uuid/' + str(
                            usb_uuid) + ' isofrom_system=/multibootusb/' + os.path.splitext(iso_name)[0] + '/'+ str(iso_name), string, flags=re.I)
                elif distro == "pclinuxos":
                    string = re.sub(r'livecd=',
                                    'fromusb livecd=' + '/multibootusb/' + os.path.splitext(iso_name)[0] + '/',
                                    string)
                    string = re.sub(r'prompt', '#prompt', string)
                    string = re.sub(r'ui gfxboot.com', '#ui gfxboot.com', string)
                    string = re.sub(r'timeout', '#timeout', string)
                elif distro == "porteus" or distro == "wifislax":
                    string = re.sub(r'initrd=',
                                    'from=' + '/multibootusb/' + os.path.splitext(iso_name)[0] + ' initrd=', string)
                elif distro == "hbcd":
                    string = re.sub(r'/HBCD', '/multibootusb/' + os.path.splitext(iso_name)[0] + '/HBCD', string)
                elif distro == "zenwalk":
                    string = re.sub(r'initrd=', 'from=/multibootusb/' + os.path.splitext(iso_name)[
                        0] + '/' + iso_name + ' initrd=', string)
                elif distro == "mageialive":
                    string = re.sub(r'LABEL=\S*', 'LABEL=' + usb_label, string)
                elif distro == "antix":
                    string = re.sub(r'APPEND', 'image_dir=/multibootusb/' + os.path.splitext(iso_name)[0], string)
                elif distro == "solydx":
                    string = re.sub(r'live-media-path=', 'live-media-path=/multibootusb/' + os.path.splitext(iso_name)[0], string)
                elif distro == "salix-live":
                    string = re.sub(r'iso_path', '/multibootusb/' + os.path.splitext(iso_name)[0] + '/' + iso_name, string)

                config_file = open(cfg_file, "wb")
                config_file.write(string)
                config_file.close()

    # Patch for Ubuntu 14.10 and above which uses syslinux version 6
    if distro == "ubuntu" and config.sys_version == "6":
        print "Applying Ubuntu patch..."
        for module in os.listdir(os.path.join(usb_mount_path, "multibootusb", os.path.splitext(iso_name)[0], "isolinux")):
            if module.endswith(".c32"):
                if os.path.exists(os.path.join(usb_mount_path, "multibootusb", os.path.splitext(iso_name)[0], "isolinux", module)):
                    try:
                        os.remove(os.path.join(usb_mount_path, "multibootusb", os.path.splitext(iso_name)[0], "isolinux", module))
                        print "Copying " + module
                        shutil.copy(gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "modules", "ubuntu_patch", module)),
                                os.path.join(usb_mount_path, "multibootusb", os.path.splitext(iso_name)[0], "isolinux", module))
                    except:
                        print "Could not copy " + module
    sys_cfg_file = os.path.join(str(usb_mount_path), "multibootusb", "syslinux.cfg")
    update_main_syslinux_cfg_file(distro, usb_disk, iso_name, sys_cfg_file, iso_cfg_ext_dir, iso_link)


def update_main_syslinux_cfg_file(distro, usb_disk, iso_name, sys_cfg_file, iso_cfg_ext_dir, iso_link):
    import shutil
    import iso
    import gen_fun
    usb_details = usb.usb_details(usb_disk)
    usb_mount_path = usb_details['mount']
    usb_uuid = usb_details['uuid']
    print "Updating main syslinux config file..."
    if os.path.exists(sys_cfg_file):

        if distro == "hbcd":
            if os.path.exists(usb_mount_path + "multibootusb", "menu.lst"):
                config_file = open(os.path.exists(usb_mount_path + "multibootusb", "menu.lst"), "wb")
                string = re.sub(r'/HBCD', '/multibootusb/' + os.path.splitext(iso_name)[0] + '/HBCD', config_file)
                config_file.write(string)
                config_file.close()

        if distro == "Windows":
            if os.path.exists(sys_cfg_file):
                config_file = open(sys_cfg_file, "a")
                config_file.write("#start " + os.path.splitext(iso_name)[0] + "\n")
                config_file.write("LABEL " + os.path.splitext(iso_name)[0] + "\n")
                config_file.write("MENU LABEL " + os.path.splitext(iso_name)[0] + "\n")
                config_file.write("KERNEL chain.c32 hd0 1 ntldr=/bootmgr" + "\n")
                config_file.write("#end " + os.path.splitext(iso_name)[0] + "\n")
                config_file.close()

        else:
            config_file = open(sys_cfg_file, "a")
            config_file.write("#start " + os.path.splitext(iso_name)[0] + "\n")
            config_file.write("LABEL " + os.path.splitext(iso_name)[0] + "\n")
            config_file.write("MENU LABEL " + os.path.splitext(iso_name)[0] + "\n")
            if distro == "salix-live":
                config_file.write(
                    "LINUX " + '/multibootusb/' + os.path.splitext(iso_name)[0] + '/boot/grub2-linux.img' + "\n")
            elif distro == "pclinuxos":
                config_file.write("kernel " + '/multibootusb/' + os.path.splitext(iso_name)[0] + '/isolinux/vmlinuz' + "\n")
                config_file.write("append livecd=livecd root=/dev/rd/3 acpi=on vga=788 keyb=us vmalloc=256M nokmsboot "
                                  "fromusb root=UUID=" + usb_uuid + " bootfromiso=/multibootusb/" +
                                  os.path.splitext(iso_name)[0] +"/" + iso_name + " initrd=/multibootusb/"
                                  + os.path.splitext(iso_name)[0] + '/isolinux/initrd.gz' + "\n")
            else:
                if distro == "ubuntu" and config.sys_version == "6":
                    config_file.write("CONFIG " + "/multibootusb/" + os.path.splitext(iso_name)[0] +
                                      "/isolinux/isolinux.cfg" + "\n")
                    config_file.write("APPEND " + "/multibootusb/" + os.path.splitext(iso_name)[0] +
                                      "/isolinux" + "\n")
                else:
                    distro_syslinux_install_dir = gen_fun.install_dir(iso_link, usb_mount_path) + iso.isolinux_bin_dir(iso_link)
                    distro_syslinux_install_dir = distro_syslinux_install_dir.replace(usb_mount_path, '')
                    distro_sys_install_bs = distro_syslinux_install_dir + '/' + distro + '.bs'
                    distro_sys_install_bs = "/" + distro_sys_install_bs.replace("\\", "/")  #  Windows path issue.
                    config_file.write("BOOT " + distro_sys_install_bs.replace("//", "/") + "\n")
            config_file.write("#end " + os.path.splitext(iso_name)[0] + "\n")
            config_file.close()

    for dirpath, dirnames, filenames in os.walk(iso_cfg_ext_dir):
        for f in filenames:
            if f.endswith("isolinux.cfg"):
                shutil.copy2(os.path.join(dirpath, f), os.path.join(dirpath, "syslinux.cfg"))