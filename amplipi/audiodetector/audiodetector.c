/*
 * AmpliPi Home Audio
 * Copyright (C) 2022 MicroNova LLC
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
/*
 * Analog RCA input audio detector.
 * Communicates with the MCP3008 ADC on the Preamp board to read the peak-detect
 * circuitry. Writes to file whether audio is playing or not, per-channel.
 */

#include <errno.h>
#include <fcntl.h>
#include <linux/spi/spidev.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

#define STATUS_FILE_PATH "rca_status"
#define SPIDEV_PATH      "/dev/spidev1.1"
#define SPI_CLOCK_HZ     3600000
#define NUM_CHANNELS     8

bool abort_ = false;

typedef union {
  struct {
    uint16_t ch3l;
    uint16_t ch3r;
    uint16_t ch2l;
    uint16_t ch2r;
    uint16_t ch1l;
    uint16_t ch1r;
    uint16_t ch0l;
    uint16_t ch0r;
  };
  uint16_t vals[NUM_CHANNELS];
} AdcData;

typedef union {
  struct {
    uint8_t ch0l : 1;
    uint8_t ch0r : 1;
    uint8_t ch1l : 1;
    uint8_t ch1r : 1;
    uint8_t ch2l : 1;
    uint8_t ch2r : 1;
    uint8_t ch3l : 1;
    uint8_t ch3r : 1;
  };
  uint8_t all;
} AudioStatus;

void sigint_handler(int sig) {
  abort_ = true;
}

bool register_sig_handler() {
  struct sigaction sa;
  memset(&sa, 0, sizeof(sa));
  sa.sa_handler = sigint_handler;
  if (sigaction(SIGINT, &sa, NULL) < 0) {
    perror("sigaction(SIGINT)");
    return false;
  }
  // TODO: What all should be handled?
  if (sigaction(SIGTERM, &sa, NULL) < 0) {
    perror("sigaction(SIGTERM)");
    return false;
  }
  return true;
}

bool open_storage(const char *path, int *fd) {
  // TODO: O_NOATIME?
  *fd = open(path, O_RDWR | O_CREAT | O_DSYNC, 0644);
  if (*fd < 0) {
    perror("open(file)");
    return false;
  }
  return true;
}

bool write_data(int fd, AudioStatus *status) {
  static AudioStatus status_previous = {.all = 0};
  // Only write data on change
  if (status->all != status_previous.all) {
    lseek(fd, 0, SEEK_SET);
    if (write(fd, status, 1) != 1) {
      perror("write");
      return false;
    }
    status_previous.all = status->all;
  }
  return true;
}

bool close_storage(int fd) {
  int result = close(fd);
  if (result < 0) {
    perror("close(file)");
    return false;
  }
  return true;
}

bool measure(AdcData *data) {
  struct spi_ioc_transfer tr[NUM_CHANNELS] = {};
  uint32_t                tx[NUM_CHANNELS] = {};
  uint32_t                rx[NUM_CHANNELS] = {};

  for (size_t i = 0; i < NUM_CHANNELS; i++) {
    tx[i]           = 0x008001 | (i << 12);  // Sends 0x01, 0x80, 0x00
    tr[i].tx_buf    = (uintptr_t)&tx[i];
    tr[i].rx_buf    = (uintptr_t)&rx[i];
    tr[i].len       = 3;
    tr[i].speed_hz  = SPI_CLOCK_HZ;
    tr[i].cs_change = 1;
  }

  // Unset cs_change for the last transfer or we lose the first read of the next
  // block.
  tr[NUM_CHANNELS - 1].cs_change = 0;

  int spi_fd = open(SPIDEV_PATH, O_RDWR);
  if (spi_fd < 0) {
    perror("open(spi)");
    memset(data, 0, sizeof(AdcData));
    return false;
  }

  /* This is the default, but leaving here as reference in case that changes.
   * uint32_t mode = SPI_MODE_0;
   * ioctl(spi_fd, SPI_IOC_WR_MODE, &mode);
   */

  if (ioctl(spi_fd, SPI_IOC_MESSAGE(NUM_CHANNELS), tr) < 0) {
    perror("ioctl()");
  }

  // ADC channel 7 = RCA 0 Right, ADC channel 6 = RCA 0 Left
  // ADC channel 5 = RCA 1 Right, etc...
  for (size_t i = 0; i < NUM_CHANNELS; i++) {
    data->vals[i] = (rx[i] & 0x300) + ((rx[i] >> 16) & 0xFF);  // rx[i] >> 8;
  }

  close(spi_fd);
  return true;
}

void process(AdcData *raw_data, AdcData *baseline, AudioStatus *status) {
  for (size_t i = 0; i < sizeof(AdcData) / sizeof(raw_data->vals[0]); i++) {
    if (raw_data->vals[i] < baseline->vals[i]) {
      baseline->vals[i] = raw_data->vals[i];
    }
  }
  status->ch0l = (raw_data->ch0l - baseline->ch0l) > 10;
  status->ch0r = (raw_data->ch0r - baseline->ch0r) > 10;
  status->ch1l = (raw_data->ch1l - baseline->ch1l) > 10;
  status->ch1r = (raw_data->ch1r - baseline->ch1r) > 10;
  status->ch2l = (raw_data->ch2l - baseline->ch2l) > 10;
  status->ch2r = (raw_data->ch2r - baseline->ch2r) > 10;
  status->ch3l = (raw_data->ch3l - baseline->ch3l) > 10;
  status->ch3r = (raw_data->ch3r - baseline->ch3r) > 10;
}

void print_data(AdcData *data) {
  printf("{ %u, %u, %u, %u, %u, %u, %u, %u }\n", data->ch0l, data->ch0r,
         data->ch1l, data->ch1r, data->ch2l, data->ch2r, data->ch3l,
         data->ch3r);
  // fflush(stdout);
}

int main(int argc, char **argv) {
  bool success = register_sig_handler();
  if (!success) {
    fprintf(stderr, "Failed to register SIGINT handler\n");
    return EXIT_FAILURE;
  }

  int status_fd;
  success = open_storage(STATUS_FILE_PATH, &status_fd);
  if (!success) {
    fprintf(stderr, "Failed to create/open status file\n");
    return EXIT_FAILURE;
  }

  AdcData baseline;  // Minimum values ever recorded
  memset(&baseline, 0xFF, sizeof(AdcData));
  AdcData     raw_data;
  AudioStatus status;
  while (1) {
    success = measure(&raw_data);
    if (!success) {
      fprintf(stderr, "Failed to read ADC\n");
      return EXIT_FAILURE;
    }

    process(&raw_data, &baseline, &status);

    success = write_data(status_fd, &status);
    if (!success) {
      fprintf(stderr, "Failed to write data\n");
      return EXIT_FAILURE;
    }

    AdcData processed_data;
    for (size_t i = 0; i < sizeof(raw_data) / sizeof(raw_data.vals[0]); i++) {
      processed_data.vals[i] = raw_data.vals[i] - baseline.vals[i];
    }
    // print_data(&processed_data);
    sleep(1);  // TODO: Timer
    if (abort_) {
      // TODO: delete file and/or write 0x00
      return close_storage(status_fd) ? EXIT_SUCCESS : EXIT_FAILURE;
    }
  };
  return EXIT_FAILURE;  // Should never reach here
}
