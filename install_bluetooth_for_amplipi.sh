# Install Bluetooth Support for Amplipi
# Partial setup instructions from: https://gist.github.com/Pindar/e259bec5c3ab862f4ff5f1fbcb11bfc1#initial-setup

# Run as: sudo .\install_bluetooth_for_amplipi.sh

apt-get install -y libsndfile1 libsndfile1-dev libbluetooth-dev bluealsa python-dbus libasound2-dev git autotools-dev automake libtool m4

# For better audio quality, build bluealsa manually after installing fdk-aac and the latest version of bluez 5.58
# Install aacplus decoder
#sudo apt-get install autoconf libtool -y
#mkdir ffmpeg
#cd ffmpeg
#wget -O fdk-aac.zip https://github.com/mstorsjo/fdk-aac/zipball/master
#unzip fdk-aac.zip
#cd mstorsjo-fdk-aac*
#autoreconf -fiv
#./configure --prefix="$HOME/ffmpeg_build" --disable-shared
#sudo make
#sudo make install
#export PKG_CONFIG_PATH=/home/pi/ffmpeg_build/lib/pkgconfig

# Upgrade bluez to latest version
#Current disabled as buster works fine with Bluez 5.50
#sudo apt-get install libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev -y
#cd ~
#wget http://www.kernel.org/pub/linux/bluetooth/bluez-5.58.tar.xz
#tar xvf bluez-5.58.tar.xz && cd bluez-5.58
#./configure --prefix=/usr --mandir=/usr/share/man --sysconfdir=/etc --localstatedir=/var --enable-experimental
#make -j4
#sudo make install


##Edit /etc/bluetooth/main.conf:
cat <<'EOF' > /etc/bluetooth/main.conf
[General]
Name = AmpliPi Bluetooth
Class = 0x200400
DiscoverableTimeout = 0
[Policy]
AutoEnable=true
EOF

# Add -a2dp-source and a2dp-sink to bluealsa.service file: /lib/systemd/system/bluealsa.service. Make a backup of the file first
cp /lib/systemd/system/bluealsa.service ~/bluealsa.service.backup
cat <<'EOF' > /lib/systemd/system/bluealsa.service
[Unit]
Description=BluezALSA proxy
Requires=bluetooth.service
After=bluetooth.service

[Service]
Type=simple
User=root
ExecStart=/usr/bin/bluealsa -p a2dp-source -p a2dp-sink

EOF

#---------------------------------------------------------------------------------------------------------------#

# Install SBC
cd /home/pi

git clone https://git.kernel.org/pub/scm/bluetooth/sbc.git
cd sbc
./bootstrap-configure
./configure
make
make install

#---------------------------------------------------------------------------------------------------------------#

# Add pi user to bluetooth group so we don't need to run sudo
usermod -G bluetooth -a pi

cd /home/pi
cp a2dp-agent /usr/local/bin
chmod +x /usr/local/bin/a2dp-agent

cp bt-agent-a2dp.service /etc/systemd/system

##Enable and start services (these services should always be running):
systemctl enable bluetooth
systemctl enable bluealsa
systemctl enable bt-agent-a2dp.service # This service is used to automatically allow bluetooth devices to connect)

reboot now

# Extra, should be started on reboot
systemctl start bluetooth
systemctl start bluealsa
systemctl start bt-agent-a2dp.service
