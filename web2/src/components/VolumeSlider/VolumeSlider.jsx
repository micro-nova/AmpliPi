
import Slider from "@mui/material/Slider";
import { useState, useEffect } from "react";
import './VolumeSlider.scss'

const UPDATE_INTERVAL = 1000

const VolumeSlider = ({getValue, onChange}) => {
  const [value, setValue] = useState(getValue());

  return (
    useEffect(() => {
      const interval = setInterval(() => {
        setValue(getValue());
      }, UPDATE_INTERVAL);
      return () => clearInterval(interval);
    }, []),
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
