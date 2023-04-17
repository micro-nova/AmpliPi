import Slider from "@mui/material/Slider";
import './VolumeSlider.scss'
import VolumeMuteIcon from '@mui/icons-material/VolumeMute';
import VolumeDownIcon from '@mui/icons-material/VolumeDown';
import VolumeOffIcon from '@mui/icons-material/VolumeOff';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';

const VolIcon = ({vol, mute}) => {
  if (mute) {
    return <VolumeOffIcon fontSize="2rem" className="volume-slider-icon volume-slider-mute"/>
  } else if (vol <= 0.2) {
    return <VolumeMuteIcon fontSize="2rem" className="volume-slider-icon"/>
  } else if (vol <= 0.5) {
    return <VolumeDownIcon fontSize="2rem" className="volume-slider-icon"/>
  } else {
    return <VolumeUpIcon fontSize="2rem" className="volume-slider-icon"/>
  }

}
const VolumeSlider = ({vol, mute, setVol, setMute}) => {

  return (
    <div className="volume-slider-container">
      <div onClick={()=>{setMute(!mute)}}>
        <VolIcon vol={vol} mute={mute}/>
      </div>
      <Slider
        className="volume-slider"
        min={0}
        step={0.01}
        max={1}
        value={vol}
        onChange={(_, val)=>{setVol(val)}}
      />
    </div>
  );
}

export default VolumeSlider;
