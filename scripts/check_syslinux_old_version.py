__author__ = 'sundar'
import re
import string

included_syslinux4_version = "SYSLINUX 4.07"
included_syslinux5_version = "SYSLINUX 5.10"
#included_syslinux6_version = "SYSLINUX 6.03"
included_syslinux6_version = "6.02"

def strings(filename, min=4):
        # function to extract printable character from binary file.
        with open(filename, "rb") as f:
            result = ""
            for c in f.read():
                if c in string.printable:
                    result += c
                    continue
                if len(result) >= min:
                    yield result
                result = ""
distro_bin = "/home/sundar/.multibootusb/syslinux/bin/syslinux6"
sl = list(strings(distro_bin))
for strin in sl:
    if re.search(r'SYSLINUX ', strin):
        #print strin
        #print re.findall('\d+', strin)
        #print [int(s) for s in strin.split() if s.isdigit()]
        print strin.split()[1]
        installed_version = strin.split()[1]
        if installed_version == included_syslinux6_version:
            print "Found matching version."
            break
        else:
            print "Not matching with installed version."

