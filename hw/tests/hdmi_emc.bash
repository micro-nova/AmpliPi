#!/usr/bin/env bash
# Displays scrolling H's on the connected HDMI monitor
# for ANSI C63.4 EMC compliance testing

trap 'exit 0' SIGINT SIGTERM

fbdev=/dev/fb0
fg_color="\xFF\xFF\xFF\x00" # white
bg_color="\x00\x00\x00\x00" # black

# Get screenbuffer parameters
width=$(cat /sys/class/graphics/fb0/virtual_size | cut -d, -f1)
height=$(cat /sys/class/graphics/fb0/virtual_size | cut -d, -f2)
echo "Screen resolution: ${width}x${height}"

bits_per_pixel=$(cat /sys/class/graphics/fb0/bits_per_pixel)
bpp=$(( $bits_per_pixel / 8 ))
echo "Bytes per pixel: $bpp"

stride_bytes=$(cat /sys/class/graphics/fb0/stride)
stride=$(( $stride_bytes / $bpp ))
echo "Screenbuffer stride in pixels: $stride"

#cols=$(tput cols)
#lines=$(tput lines)
#echo "# columns = $cols"
#echo "# lines   = $lines"
##eval printf 'H%.0s' {1..$(($cols*$lines))}
#echo "Press [CTRL+C] to exit"
#while true; do
#  eval printf 'H%.0s' {1..$cols}
#  printf '\n'
#  sleep 0.2
#done

if [ ! -z "$DISPLAY" ]; then
  echo 'Error, must run without X server'
  exit 1
fi

char_width=8
char_height=8
cols=$(($width / $char_width))
lines=$(($height / $char_height))
function draw_h() {
  hx=$1 # Left
  hy=$2 # Top
  # # # # # # # # #
  # - - - - - - - -
  # - - # - - - # -
  # - - # - - - # -
  # - - # - - - # -
  # - - # # # # # -
  # - - # - - - # -
  # - - # - - - # -
  # - - # - - - # -
  printf "$bg_color$bg_color$bg_color$bg_color$bg_color$bg_color$bg_color$bg_color" | \
    sudo dd bs=$bpp seek=$((($hy + 0) * $stride + $hx)) of=$fbdev &>/dev/null
  printf "$bg_color$bg_color$fg_color$bg_color$bg_color$bg_color$fg_color$bg_color" | \
    sudo dd bs=$bpp seek=$((($hy + 1) * $stride + $hx)) of=$fbdev &>/dev/null
  printf "$bg_color$bg_color$fg_color$bg_color$bg_color$bg_color$fg_color$bg_color" | \
    sudo dd bs=$bpp seek=$((($hy + 2) * $stride + $hx)) of=$fbdev &>/dev/null
  printf "$bg_color$bg_color$fg_color$bg_color$bg_color$bg_color$fg_color$bg_color" | \
    sudo dd bs=$bpp seek=$((($hy + 3) * $stride + $hx)) of=$fbdev &>/dev/null
  printf "$bg_color$bg_color$fg_color$fg_color$fg_color$fg_color$fg_color$bg_color" | \
    sudo dd bs=$bpp seek=$((($hy + 4) * $stride + $hx)) of=$fbdev &>/dev/null
  printf "$bg_color$bg_color$fg_color$bg_color$bg_color$bg_color$fg_color$bg_color" | \
    sudo dd bs=$bpp seek=$((($hy + 5) * $stride + $hx)) of=$fbdev &>/dev/null
  printf "$bg_color$bg_color$fg_color$bg_color$bg_color$bg_color$fg_color$bg_color" | \
    sudo dd bs=$bpp seek=$((($hy + 6) * $stride + $hx)) of=$fbdev &>/dev/null
  printf "$bg_color$bg_color$fg_color$bg_color$bg_color$bg_color$fg_color$bg_color" | \
    sudo dd bs=$bpp seek=$((($hy + 7) * $stride + $hx)) of=$fbdev &>/dev/null
}

function draw_line() {
  lx=0
  ly=$1
  for i in {1..$cols}; do
    draw_h $((x)) $((y))
    x=$((x+$char_width))
  done
}

function draw_screen() {
  # Pixel offset, 0 to $char_height
  po=$1
  for i in {1..$}
}

#clear
draw_line 0
draw_line $char_height

offset=0
while true; do
  draw_line

done
