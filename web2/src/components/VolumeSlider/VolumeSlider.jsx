
import Slider from "@mui/material/Slider";
import { useState, useEffect } from "react";
import './VolumeSlider.scss'

const VolumeSlider = ({vol, onChange}) => {

  const [value, setValue] = useState(vol);

  return (
    // useEffect(() => {
    //   setValue(vol);
    // }, [vol]),
    <Slider
      className="volume-slider"
      min={0}
      step={0.01}
      max={1}
      value={value}
      onChange={(event, val)=>{onChange(event, val); setValue(val)}}
    />
  );
}

export default VolumeSlider;
