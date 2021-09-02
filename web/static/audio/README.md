# Test Audio files
These files are used in various audio tests to validate the audio system
## Voice generation
Specific audio was generated using https://www.text2speech.org/
## Conversion
make the downloaded audio files only play to the left or right
using the ideas from: https://trac.ffmpeg.org/wiki/AudioChannelManipulation
```bash
ffmpeg -i analog1_right.wav -ac 2 analog1_right_stereo.wav
ffmpeg -i analog1_left.wav -ac 2 analog1_left_stereo.wav
ffmpeg -i analog1_right_stereo.wav -map_channel -1 -map_channel 0.0.1 analog1.right.wav
ffmpeg -i analog1_left_stereo.wav -map_channel 0.0.0 -map_channel -1 analog1.left.wav
```
concat the left and right audio files
```bash
for s in analog digital; do
  for i in {1..4}; do
    ffmpeg -i $s$i.left.wav -i $s$i.right.wav -filter_complex "[0:a][1:a]concat=v=0:a=1,silenceremove=stop_periods=-1" $s$i.mp3
  done
done
```
