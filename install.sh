#!/usr/bin/env bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root/sudo." 1>&2
   echo "Try sudo ./install.sh" 1>&2
   exit 1
fi

echo "Checking internet connection..."
if [ "$(ping -w5 -c3 www.google.com)" ]; then
	internet="yes"
	echo "internet connection exits."
else
	echo "Unable to connect to internet. Check your internet connection."
	echo "You should have working internet connection to install dependencies."
	echo "You can still install multibootusb if you are sure that your system "
	echo "already have \"python2.7\", \"pyqt4\" and \"python-psutil\" installed."
	echo "Should I go ahead [y/n]"
	read input
	if [ $input = "n" ] || [ $input == "N" ] || [ $input == "no" ]  || [ $input == "No" ] || [ $input == "NO" ]; then
		echo "Please connect to internet and try again."
		echo "Exiting now. :-(("
		echo ""
		exit 1
	elif [ $input = "y" ] || [ $input == "Y" ] || [ $input == "yes" ]  || [ $input == "Yes" ] || [ $input == "YES" ]; then
		internet="no"
		echo "no internet connection"	
	else
		echo "Wrong option. Try installing the script again. Exiting now."
		exit 1
	fi
fi

echo "Checking distro..."

if [ "$(which pacman)" ]; then
	distro="arch"
	update_repo="pacman -Sy --noconfirm"
	install_dependency="pacman -S --needed --noconfirm python2-pyqt4 udisks python2-psutil" # Thanks Neitsab for "--needed"  argument.
elif [ "$(which yum)" ]; then
	distro="fedora"
	update_repo="yum check-update"
	install_dependency="yum install PyQt4 python-psutil -y"
elif [ "$(which apt-get)" ]; then
	distro="debian"
	update_repo="apt-get -q update"
	install_dependency="apt-get -q -y install python-qt4 python-psutil"
elif [ "$(which zypper)" ]; then
	distro="suse"
	update_repo="zypper refresh"
	install_dependency="zypper install -y python-qt4 python-psutil"	
elif [ "$(which urpmi)" ]; then
	distro="mageia"
	update_repo="urpmi.update -a"
	install_dependency="urpmi install -auto python-qt4 python-psutil"
		
	    
else
	distro="None"	
fi

if [ $internet == "yes" ] && [ $distro == "None" ]; then
	echo "Unable to find package manager type. You must install dependencies \"python-qt4\" and \"python-psutil\" manually and issue the following commands."
	echo ""
	echo ""	
	echo "cd /path/to/multibootusb/root/directory"
	echo "python2.7 setup.py install --record ./.install_files.txt"
	echo ""
	echo ""	
	exit 1
	
elif [ $internet == "yes" ]; then
    echo "Refreshing package list. This may take some time depending on your internet speed..."
	$update_repo
	echo "Installing dependency packages python-qt4 and python-psutil..."
	$install_dependency
    echo "Installing multibootusb..."
fi

if [ $internet == "no" ] || [ $internet == "yes" ]; then
    python2.7 setup.py install --record ./.install_files.txt
	echo ""
	echo ""
	echo ""	
	echo "Installation finished. Find multibootusb under system menu or run from terminal  using the following command..."	
	echo ""		
	echo "multibootusb"
	echo ""
	echo ""	
	echo "You can uninstall multibootusb at any time using follwing command (with root/sudo previlage)"
	echo ""	
	echo "./uninstall.sh"
	echo ""
	echo ""
	
fi
exit 0
