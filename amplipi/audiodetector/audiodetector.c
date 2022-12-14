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

#define STATUS_FILE_PATH    "rca_status"
#define SPIDEV_PATH         "/dev/spidev1.1"
#define SPI_CLOCK_HZ        3600000
#define NUM_CHANNELS        8
#define SAMPLES_PER_SECOND  10
#define WINDOW_SIZE_SECONDS 3
#define TIMEOUT_SECONDS     10
#define MICRO               1000000
#define CH_ACTIVE_THR       10
#define DEFAULT_BASELINE    550
#define WINDOW_SIZE         (SAMPLES_PER_SECOND * WINDOW_SIZE_SECONDS)
#define TIMEOUT_CYCLES      (SAMPLES_PER_SECOND * TIMEOUT_SECONDS)

// #define DUMP_CSV
// #define DEBUG_PRINT

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

// i would be duplicating AdcData and giving it a different name, so this is fine right?
typedef AdcData AdcTimeout;

typedef struct {
  union {
    struct {
      uint16_t ch3l[WINDOW_SIZE];
      uint16_t ch3r[WINDOW_SIZE];
      uint16_t ch2l[WINDOW_SIZE];
      uint16_t ch2r[WINDOW_SIZE];
      uint16_t ch1l[WINDOW_SIZE];
      uint16_t ch1r[WINDOW_SIZE];
      uint16_t ch0l[WINDOW_SIZE];
      uint16_t ch0r[WINDOW_SIZE];
    };
    uint16_t ch_vals[NUM_CHANNELS][WINDOW_SIZE];
    uint16_t all_vals[NUM_CHANNELS * WINDOW_SIZE];
  };
  size_t index; // rolling index into the window
} AdcWindow;

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

bool close_storage(const char *path, int fd) {
  int result = close(fd);
  if (result < 0) {
    perror("close(file)");
    return false;
  }
  // Delete output file so AmpliPi knows no status is available.
  result = remove(path);
  if (result < 0) {
    perror("remove(file)");
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

void init_window(AdcWindow *window) {
  for (size_t i = 0; i < sizeof(window->all_vals) / sizeof(window->all_vals[0]); i++)
    window->all_vals[i] = DEFAULT_BASELINE;
  window->index = 0;
}

void update_window(AdcWindow *window, AdcData *raw_data) {
  // each channel's window is a circular queue, insert the raw data into the current slot/index
  for (size_t i = 0; i < NUM_CHANNELS; i++) {
    window->ch_vals[i][window->index] = raw_data->vals[i];
  }
  window->index = (window->index + 1) % WINDOW_SIZE;
}

void process(AdcData *max_data, AdcWindow *window, AdcData *baseline, AdcTimeout *timeout,
             AudioStatus *status) {
  // Update baseline
  for (size_t i = 0; i < sizeof(AdcData) / sizeof(max_data->vals[0]); i++) {
    if (max_data->vals[i] < baseline->vals[i]) {
      baseline->vals[i] = max_data->vals[i];
    }
  }
  // Update status
  status->all = 0;
  for (size_t ch = 0; ch < NUM_CHANNELS; ch++) {
    if (max_data->vals[ch] - baseline->vals[ch] > CH_ACTIVE_THR) {
      timeout->vals[ch] = TIMEOUT_CYCLES;
      status->all = status->all | (1 << (NUM_CHANNELS - ch - 1));
    } else if (timeout->vals[ch] > 0) {
      timeout->vals[ch]--;
      status->all = status->all | (1 << (NUM_CHANNELS - ch - 1));
    }
  }
}

// Given the window of past raw data, populate maxvals with the max along
// channels
void compute_window_max(AdcWindow *window, AdcData *maxvals) {
  // iterate through channels
  for (size_t ch = 0; ch < sizeof(maxvals->vals) / sizeof(maxvals->vals[0]); ch++) {
    // iterate through samples
    maxvals->vals[ch] = 0;
    for (size_t s = 0; s < sizeof(window->ch0l) / sizeof(window->ch0l[0]); s++) {
      uint16_t curr_val = window->ch_vals[ch][s];
      if (curr_val > maxvals->vals[ch]) {
        maxvals->vals[ch] = curr_val;
      }
    }
  }
}

void print_data(AdcData *data) {
  printf("{ %u, %u, %u, %u, %u, %u, %u, %u }\n", data->ch0l, data->ch0r,
         data->ch1l, data->ch1r, data->ch2l, data->ch2r, data->ch3l,
         data->ch3r);
  // fflush(stdout);
}

void print_status(AudioStatus *status) {
  printf("{ %u, %u, %u, %u, %u, %u, %u, %u }\n", status->ch0l, status->ch0r,
         status->ch1l, status->ch1r, status->ch2l, status->ch2r, status->ch3l,
         status->ch3r);
}

void print_csv_header(FILE *csv) {
  fprintf(csv,
          "ch0l,ch0r,ch1l,ch1r,ch2l,ch2r,ch3l,ch3r,s0l,s0r,s1l,s1r,s2l,s2r,s3l,"
          "s3r,\n");
}

void print_to_csv(AdcData *data, AudioStatus *status, FILE *csv) {
#ifdef DUMP_CSV
  fprintf(csv, "%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,\n", data->ch0l,
          data->ch0r, data->ch1l, data->ch1r, data->ch2l, data->ch2r,
          data->ch3l, data->ch3r, status->ch0l, status->ch0r, status->ch1l,
          status->ch1r, status->ch2l, status->ch2r, status->ch3l, status->ch3r);
#endif
}

FILE *open_csv() {
#ifdef DUMP_CSV
  FILE *f_csv;
  f_csv = fopen("raw_dump.csv", "w+");
  print_csv_header(f_csv);
  return f_csv;
#else
  return NULL;
#endif
}

void close_csv(FILE *f_csv) {
#ifdef DUMP_CSV
  fclose(f_csv);
#endif
}

void print_values(AdcData *baseline, AdcData *raw_data, AdcData *max_data,
                  AudioStatus *status) {
#ifdef DEBUG_PRINT
  printf("baseline:    ");
  print_data(baseline);
  printf("raw data:    ");
  print_data(raw_data);
  printf("window max:  ");
  print_data(max_data);
  printf("status:      ");
  print_status(status);
#endif
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

  AdcData     baseline;  // Minimum values ever recorded (of window max)
  AdcTimeout  timeout;
  for (size_t i = 0; i < sizeof(AdcData) / sizeof(baseline.vals[0]); i++) {
    baseline.vals[i] = DEFAULT_BASELINE;
    timeout.vals[i] = 0;
  }
    
  AdcWindow   window;
  AdcData     raw_data;
  AdcData     max_data;
  AudioStatus status;

  FILE       *f_csv = open_csv();

  init_window(&window);

  while (1) {
    success = measure(&raw_data);
    if (!success) {
      fprintf(stderr, "Failed to read ADC\n");
      return EXIT_FAILURE;
    }
    update_window(&window, &raw_data);
    compute_window_max(&window, &max_data);
    process(&max_data, &window, &baseline, &timeout, &status);
    print_values(&baseline, &raw_data, &max_data, &status);
    print_to_csv(&max_data, &status, f_csv);

    success = write_data(status_fd, &status);
    if (!success) {
      fprintf(stderr, "Failed to write data\n");
      return EXIT_FAILURE;
    }

    usleep(MICRO / SAMPLES_PER_SECOND);
    if (abort_) {
      close_csv(f_csv);
      bool result = close_storage(STATUS_FILE_PATH, status_fd);
      return result ? EXIT_SUCCESS : EXIT_FAILURE;
    }
  };
  return EXIT_FAILURE;  // Should never reach here
}
