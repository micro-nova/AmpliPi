# Test Audio files
These files are used in various audio tests to validate the audio system
## Voice generation
Specific audio was generated using https://www.text2speech.org/
## Conversion
make the downloaded audio files only play to the left or right
using the ideas from: https://trac.ffmpeg.org/wiki/AudioChannelManipulation
```bash
digitals='digital1 digital2 digital3 digital4'
analogs='analog1 analog2 analog3 analog4'
for type in aux_in $digitals $analogs; do
  echo $type
  left_audio="${type}_left.wav"
  right_audio="${type}_right.wav"
  if [[ -e $right_audio ]]; then
    ffmpeg -i $right_audio -ac 2 "${type}_right_stereo.wav"
    ffmpeg -i "${type}_right_stereo.wav" -map_channel -1 -map_channel 0.0.1 $type.right.wav
  fi
  if [[ -e $left_audio ]]; then
    ffmpeg -i $left_audio -ac 2 "${type}_left_stereo.wav"
    ffmpeg -i "${type}_left_stereo.wav" -map_channel 0.0.0 -map_channel -1 $type.left.wav
  fi
done
```
concat the left and right audio files and trim silence in audio to speed up playback
```bash
if [[ -e aux_in.left.wav ]] && [[ -e aux_in.right.wav ]]; then
  ffmpeg -i aux_in.left.wav -i aux_in.right.wav -filter_complex "[0:a][1:a]concat=v=0:a=1,silenceremove=stop_periods=-1" aux_in.mp3
fi
for s in analog digital; do
  for i in {1..4}; do
    ffmpeg -i $s$i.left.wav -i $s$i.right.wav -filter_complex "[0:a][1:a]concat=v=0:a=1,silenceremove=stop_periods=-1" $s$i.mp3
  done
done
```
