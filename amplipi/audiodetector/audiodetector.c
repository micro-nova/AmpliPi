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

#define SPIDEV_PATH  "/dev/spidev1.1"
#define SPI_CLOCK_HZ 3600000
#define NUM_CHANNELS 8

bool abort_ = false;

void measure(uint16_t *data) {
  struct spi_ioc_transfer tr[NUM_CHANNELS] = {};
  uint32_t                tx[NUM_CHANNELS] = {};
  uint32_t                rx[NUM_CHANNELS] = {};

  for (size_t i = 0; i < NUM_CHANNELS; i++) {
    tx[i]           = 0x008001 | (i << 12);  // Sends 0x01, 0x80, 0x00
    tr[i].tx_buf    = (uint32_t)&tx[i];
    tr[i].rx_buf    = (uint32_t)&rx[i];
    tr[i].len       = 3;
    tr[i].speed_hz  = SPI_CLOCK_HZ;
    tr[i].cs_change = 1;
  }

  // Unset cs_change for the last transfer or we lose the first read of the next
  // block.
  tr[NUM_CHANNELS - 1].cs_change = 0;

  int fd = open(SPIDEV_PATH, O_RDWR);
  if (fd < 0) {
    perror("open()");
    memset(data, 0, NUM_CHANNELS * sizeof(data[0]));
    return;
  }

  /* This is the default, but leaving here as reference in case that changes.
   * uint32_t mode = SPI_MODE_0;
   * ioctl(fd, SPI_IOC_WR_MODE, &mode);
   */

  if (ioctl(fd, SPI_IOC_MESSAGE(NUM_CHANNELS), tr) < 0) {
    perror("ioctl()");
  }

  for (size_t i = 0; i < NUM_CHANNELS; i++) {
    data[i] = (rx[i] & 0x300) + ((rx[i] >> 16) & 0xFF);  // rx[i] >> 8;
  }

  close(fd);
  return;
}

void print_data(uint16_t *data) {
  printf("{ %u", data[0]);
  for (size_t i = 1; i < NUM_CHANNELS; i++) {
    printf(", %u", data[i]);
  }
  printf(" }\n");
}

void sigint_handler(int sig) {
  abort_ = true;
}

int register_sig_handler() {
  struct sigaction sa;
  memset(&sa, 0, sizeof(sa));
  sa.sa_handler = sigint_handler;
  if (sigaction(SIGINT, &sa, NULL) < 0) {
    perror("sigaction(SIGINT)");
    return EXIT_FAILURE;
  }
  // TODO: What all should be handled?
  if (sigaction(SIGTERM, &sa, NULL) < 0) {
    perror("sigaction(SIGTERM)");
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}

int main(int argc, char **argv) {
  int success = register_sig_handler();
  if (success == EXIT_FAILURE) {
    fprintf(stderr, "Failed to register SIGINT handler\n");
    return EXIT_FAILURE;
  }

  uint16_t data[NUM_CHANNELS];
  while (1) {
    measure(data);
    print_data(data);
    sleep(1);
    if (abort_) {
      return EXIT_SUCCESS;
    }
  };
  return EXIT_FAILURE;  // Should never reach here
}
