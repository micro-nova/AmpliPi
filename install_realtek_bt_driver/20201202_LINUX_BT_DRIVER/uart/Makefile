DRV_SRC_DIR	:= bluetooth_uart_driver
MDL_DIR	:= /lib/modules/$(shell uname -r)
DRV_DIR	:= $(MDL_DIR)/kernel/drivers/bluetooth

TOOL_SRC_DIR := rtk_hciattach
TOOL_DIR := /usr/sbin

install:
	mkdir -p $(DRV_DIR)
	- rmmod hci_uart
	make -C $(DRV_SRC_DIR)
	#mv -n $(DRV_DIR)/hci_uart.ko $(FW_DIR)/hci_uart.bk
	cp -f $(DRV_SRC_DIR)/hci_uart.ko $(DRV_DIR)/hci_uart.ko
	depmod -a $(shell uname -r)
	make -C $(DRV_SRC_DIR) clean
	echo "make hci_uart_driver success!"
	make -C $(TOOL_SRC_DIR)
	cp -f $(TOOL_SRC_DIR)/rtk_hciattach $(TOOL_DIR)/rtk_hciattach
	make -C $(TOOL_SRC_DIR) clean
	echo "make rtk_hciattach success!"

uninstall:
	mv -f $(FW_DIR)/hci_uart.bk $(DRV_DIR)/hci_uart.ko
	depmod -a $(shell uname -r)
	- rm -f $(FW_DIR)/hci_uart.bk
	rm -f $(FW_DIR)/rtlbt_fw
	rm -f $(FW_DIR)/rtlbt_config
	echo "uninstall hci_uart_driver success!"
	rm -f $(TOOL_DIR)/rtk_hciattach
	echo "uninstall rtk_hciattach success!"

