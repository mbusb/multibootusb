####User guide is located here http://multibootusb.org/page_guide/

What is multibootusb?
---------------------
MultiBootUSB is a cross platform* software/utility to create multi boot live Linux on a removable media i.e USB disk.
It is similar to unetbootin but many distros can be installed, provided you have enough space on the disk.
MultiBootUSB also provides an option to uninstall distro(s) at any time, if you wish.

* Only works on windows and linux

How to install?
---------------

The install.py script provided with multibootusb should take care of all dependency and install multibootusb.
Assume that you have downloaded the package named "multibootusb.tar.gz" in to your home directory.
Issue the following commands to install multibootusb:-

```
tar -xf ./multibootusb.tar.gz  
cd multibootusb  
chmod +x ./install.py  
sudo ./install.py
```

That is it. You can find multibootusb under system menu or simply launch from terminal by typing "multibootusb".
If "install.py" script fails to install multibootusb successfully then manually install following packages and rerun the install.py script:-

* mtools util-linux parted python3-qt5 python-dbus pkexec

NOTE: install.py currently supports only distros based on apt-get, yum, zypper, pacman.
You can add more if you use other package manager system and email to me for adding into upstream.
The above how to is only for linux. Windows users may download pre compiled standalone binaries/ .exe from
https://sourceforge.net/projects/multibootusb/files/

How to uninstall?
-----------------
You can uninstall multibootusb at any time using the "uninstall.py" script provided with multibootusb.

```
cd multibootusb
chmod +x ./uninstall.py
sudo ./uninstall.py
```

Website:
--------
www.multibootusb.org

Development:
-----------
https://github.com/mbusb/multibootusb

Help:
-----
Mail me at feedback.multibootusb@gmail.com for query, help, bug report or feature request.

Contributor(s)
--------------
LiQiong Lee
Ian Bruce
and many others who have given their valuable bug report/ feedback.

Author(s)
---------
MultiBootUSB is brought to you by Sundar and co-authored by Ian Bruce.
