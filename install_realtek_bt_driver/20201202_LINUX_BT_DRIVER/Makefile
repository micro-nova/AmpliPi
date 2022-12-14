FW_USB_DIR := /lib/firmware
FW_UART_DIR := /lib/firmware/rtlbt
RTKBT_FIRMWARE_DIR := rtkbt-firmware/lib/firmware
MDL_DIR	:= /lib/modules/$(shell uname -r)
DRV_DIR	:= $(MDL_DIR)/kernel/drivers/bluetooth


install:
ifeq (,$(filter usb uart all,$(INTERFACE)))
	@echo "Usage: sudo make install INTERFACE=[rtkbt_interface]"
	@echo "rtkbt_interface:"
	@echo " all	USB and UART"
	@echo " usb	USB"
	@echo " uart	UART"
	exit 1
else 
	mkdir -p $(DRV_DIR)
endif

ifneq (,$(filter usb all,$(INTERFACE)))
	@echo "Start Realtek Bluetooth USB driver installation"
	$(eval FW_FILE := rtl*_fw)
	$(eval CONFIG_FILE := rtl*_config)
	$(eval FW_DIR := $(FW_USB_DIR))
	$(eval SRC_ROOT_DIR := usb)
	mkdir -p $(FW_DIR)
	@echo "Copy $(RTKBT_FIRMWARE_DIR)/$(FW_FILE) to $(FW_DIR)"
	cp -a $(RTKBT_FIRMWARE_DIR)/$(FW_FILE) $(FW_DIR)
	@echo "Copy $(RTKBT_FIRMWARE_DIR)/$(CONFIG_FILE) $(FW_DIR)"
	cp -a $(RTKBT_FIRMWARE_DIR)/$(CONFIG_FILE) $(FW_DIR)
	make -C $(SRC_ROOT_DIR) install
endif

ifneq (,$(filter uart all,$(INTERFACE)))
	@echo "Start Realtek Bluetooth UART driver installation"
	$(eval FW_FILE := rtlbt/rtl*_fw)
	$(eval CONFIG_FILE := rtlbt/rtl*_config)
	$(eval FW_DIR := $(FW_UART_DIR))
	$(eval SRC_ROOT_DIR := uart)
	mkdir -p $(FW_DIR)
	@echo "Copy $(RTKBT_FIRMWARE_DIR)/$(FW_FILE) to $(FW_DIR)"
	cp -a $(RTKBT_FIRMWARE_DIR)/$(FW_FILE) $(FW_DIR)
	@echo "Copy $(RTKBT_FIRMWARE_DIR)/$(CONFIG_FILE) $(FW_DIR)"
	cp -a $(RTKBT_FIRMWARE_DIR)/$(CONFIG_FILE) $(FW_DIR)
	make -C $(SRC_ROOT_DIR) install
endif
