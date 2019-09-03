mount -t /dev/sdX /mnt
mkdir -p /mnt/boot
grub-install --force --no-floppy --boot-directory=/mnt/boot /dev/sdX
mkdir -p /mnt/boot/grub
