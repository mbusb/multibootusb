#!/usr/bin/env bash
# Thanks Neitsab for typo correction.
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root/sudo" 1>&2
   echo "Try sudo ./uninstall.sh" 1>&2
   exit 1
fi

echo "Going to uninstall multibootusb..."

#cat ./.install_files.txt | xargs sudo rm -rf
for data_path in `cat ./.install_files.txt`
	do
		echo "Removing " ${data_path}
		rm -rf ${data_path}
	done

echo "multibootusb is successfully unistalled..."
