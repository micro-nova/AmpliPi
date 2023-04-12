import Slider from "@mui/material/Slider";
import { useState, useEffect } from "react";
import './VolumeSlider.scss'
import { getSourceZones } from "@/pages/Home/Home"
import { useStatusStore } from "@/App"

const getPlayerVol = (sourceId, zones) => {
  let vol = 0;
  let n = 0;
  for (const i of getSourceZones(sourceId, zones)) {
    n += 1;
    vol += i.vol_f;
  }

  const avg = vol / n;

  if (isNaN(avg)) {
    return 0;
  } else {
    return avg;
  }
};

export const applyPlayerVol = (vol, zones, sourceId, apply) => {
  let delta = vol - getPlayerVol(sourceId, zones);

  for (let i of getSourceZones(sourceId, zones)) {
    let set_pt = Math.max(0, Math.min(1, i.vol_f + delta));
    apply(i.id, set_pt)
  }
}


let sendingPacketCount = 0

const VolumeSlider = ({sourceId}) => {
  const zones = useStatusStore((s) => s.status.zones)
  const setZonesVol = useStatusStore((s) => s.setZonesVol)

  const setPlayerVolRaw = (vol) => applyPlayerVol(vol, zones, sourceId, (zone_id, new_vol) => {

    sendingPacketCount += 1
    fetch(`/api/zones/${zone_id}`, {
        method: "PATCH",
        headers: {
          "Content-type": "application/json",
        },
        body: JSON.stringify({ vol_f: new_vol }),
      }).then(() => {sendingPacketCount -= 1})
  })

  const setPlayerVol = (vol) => {
    if (sendingPacketCount <= 0) {
      setPlayerVolRaw(vol)
    }
  }

  const value = getPlayerVol(sourceId, zones)

  const setValue = (vol) => {
    setZonesVol(vol, zones, sourceId)
  }

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
      onChange={(event, val)=>{setPlayerVol(val); setValue(val)}}
    />
  );
}

export default VolumeSlider;
