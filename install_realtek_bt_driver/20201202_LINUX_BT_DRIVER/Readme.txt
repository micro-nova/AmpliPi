===============
  TITLE
===============

The document describes how to support Realtek Bluetooth UART and USB driver in Linux system.

===============
  REQUIREMENT
===============

The supported kernel version is 2.6.32 - 5.7.1

=============================
  QUICKLY INSTALL AUTOMATICALLY
=============================

  $ sudo make install INTERFACE=all
or
  $ sudo make install INTERFACE=usb
or
  $ sudo make install INTERFACE=uart

===============
  FOR UART I/F
===============

-The default serial protocol of Realtek Bluetooth chip is Three-wire (H5) protocol.

-The default initial baud rate is 115200.

-Installation

  To support Three-wire (H5) protocol, you need to install Realtek hci_uart driver
  and rtk_hciattach tool.

  1. Make sure your UART setting is correct.
     host tx  - controller rx
     host rx  - controller tx
     host rts - controller cts
     host cts - ground
   ( host cts - controller rts ) // for RTL8822C and RTL8761B
          NC  - controller rts

  2. Install Bluetooth kernel driver and rtk_hciattach tool
   $ cd uart
   $ sudo make install

  3. Copy the right FW file and config file to the correct path.
   $ sudo mkdir -p /lib/firmware/rtlbt/
   $ sudo cp rtkbt-firmware/lib/firmware/rtlbt/rtl8xxxx_fw /lib/firmware/rtlbt/
   $ sudo cp rtkbt-firmware/lib/firmware/rtlbt/rtl8xxxx_config /lib/firmware/rtlbt/

   NOTE: PLEASE REFER THE FORWARD SECTION OF FILENAME LIST TO CORRESPONDE THE FW FILENAME AND THE CONFIG FILENAME WITH THE CHIP.

  3. Initialize Realtek Bluetooth chip by rtk_hciattach
   $ sudo rtk_hciattach -n -s 115200 ttyUSB0 rtk_h5

    Tips: ttyUSB0 is serial port name in your system, you should change it
    according to hardware such as ttyS0.

-Uninstallation
   $ sudo make uninstall

- If you want to change the parameter such as baud rate and pcm settings, you
should modify rtl8xxx_config file.

===============
  FOR USB I/F
===============

-Installation

  1. Build and install USB driver, change to the driver direcotory
   $ cd usb
   $ sudo make install

  2. Copy the right FW file and config file to the correct path.
   $ sudo cp rtkbt-firmware/lib/firmware/rtl8xxxxx_fw /lib/firmware/
   $ sudo cp rtkbt-firmware/lib/firmware/rtl8xxxxx_config /lib/firmware/

   NOTE: PLEASE REFER THE FORWARD SECTION OF FILENAME LIST TO CORRESPONDE THE FW FILENAME AND THE CONFIG FILENAME WITH THE CHIP.
	   
  3. Insert Realtek Bluetooth dongle
    Check LMP subversion by the following command
    $ hciconfig -a

    Now RTK chip can be recognized by the system and bluetooth function can be used.

-Uninstallation
   $ sudo make uninstall

===============	
  FILENAME LIST
===============
	
Chip		I/F 		FW/Config Path		FW Filename		Config Filename
		for
		BT driver
------------------------------------------------------------------------------------------------
RTL8761AUV	USB		/lib/firmware/		rtl8761au_fw		rtl8761a_config

RTL8761AW 	USB		/lib/firmware/		rtl8761aw_fw		rtl8761aw_config
(RTL8761AW 
+RTL8192EU)	

RTL8761AUV      USB		/lib/firmware/		rtl8761au8192ee_fw	rtl8761a_config
+RTL8192EE
 
RTL8761AUV	USB		/lib/firmware/		rtl8761au8192ee_fw	rtl8761a_config
+RTL8812AE
 
RTL8761ATV	UART		/lib/firmware/rtlbt/	rtl8761a_fw		rtl8761a_config

RTL8761ATV
+RTL8192EE	UART		/lib/firmware/rtlbt/	rtl8761at8192ee_fw	rtl8761a_config
 
-----------------------------------------------------------------------------------------------

RTL8761BUV	USB		/lib/firmware/		rtl8761bu_fw		rtl8761bu_config

RTL8761BTV	UART		/lib/firmware/rtlbt/	rtl8761b_fw		rtl8761b_config

-----------------------------------------------------------------------------------------------

RTL8725AU	USB		/lib/firmware/		rtl8725au_fw		rtl8725au_config

RTL8725AS	UART		/lib/firmware/rtlbt/	rtl8725as_fw		rtl8725as_config

-----------------------------------------------------------------------------------------------

RTL8723BU	USB		/lib/firmware/		rtl8723b_fw		rtl8723b_config
RTL8723BE

RTL8723BS	UART		/lib/firmware/rtlbt/	rtl8723b_fw		rtl8723b_config

-----------------------------------------------------------------------------------------------

RTL8821AU	USB		/lib/firmware/		rtl8821a_fw		rtl8821a_config
RTL8821AE

RTL8821AS	UART		/lib/firmware/rtlbt/	rtl8821a_fw		rtl8821a_config

-----------------------------------------------------------------------------------------------

RTL8822BU	USB		/lib/firmware/		rtl8822bu_fw		rtl8822bu_config
RTL8822BE

RTL8822BS	UART		/lib/firmware/rtlbt/	rtl8822b_fw		rtl8822b_config

-----------------------------------------------------------------------------------------------

RTL8723DU	USB		/lib/firmware/		rtl8723du_fw		rtl8723du_config
RTL8723DE

RTL8723DS	UART		/lib/firmware/rtlbt/	rtl8723d_fw		rtl8723d_config

-----------------------------------------------------------------------------------------------

RTL8821CU	USB		/lib/firmware/		rtl8821cu_fw		rtl8821cu_config
RTL8821CE

RTL8821CS	UART		/lib/firmware/rtlbt/	rtl8821c_fw		rtl8821c_config

-----------------------------------------------------------------------------------------------

RTL8822CU	USB		/lib/firmware/		rtl8822cu_fw		rtl8822cu_config
RTL8822CE

RTL8822CS	UART		/lib/firmware/rtlbt/	rtl8822cs_fw		rtl8822cs_config

-----------------------------------------------------------------------------------------------

RTL8723FU	USB		/lib/firmware/		rtl8723fu_fw		rtl8723fu_config
RTL8723FE

RTL8723FS	UART		/lib/firmware/rtlbt/	rtl8723fs_fw		rtl8723fs_config

-----------------------------------------------------------------------------------------------

RTL8852AU	USB		/lib/firmware/		rtl8852au_fw		rtl8852au_config
RTL8852AE

RTL8852AS	UART		/lib/firmware/rtlbt/	rtl8852as_fw		rtl8852as_config

-----------------------------------------------------------------------------------------------
