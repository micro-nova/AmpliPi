import Slider from "@mui/material/Slider";
import { useState, useEffect } from "react";
import './ZoneVolumeSlider.scss'
import { getSourceZones } from "@/pages/Home/Home"
import { useStatusStore } from "@/App"

let sendingRequestCount = 0

const ZoneVolumeSlider = ({zoneId}) => {
  const zoneName = useStatusStore((s) => s.status.zones[zoneId].name)
  const volume = useStatusStore((s) => s.status.zones[zoneId].vol_f)
  const setZoneVol = useStatusStore((s) => s.setZoneVol)

  const setVol = (vol) => {

    if (sendingRequestCount <= 0) {
      sendingRequestCount += 1

      fetch(`/api/zones/${zoneId}`, {
        method: 'PATCH',
        headers: {
          'Content-type': 'application/json',
        },
        body: JSON.stringify({vol_f: vol}),
      }).then(() => {sendingRequestCount -= 1})
    }
  }

  return (
    <div className="zone-volume-container">
      {zoneName}
      <Slider
        min={0}
        step={0.01}
        max={1}
        value={volume}
        onChange={(e, val) => {setZoneVol(zoneId, val); setVol(val)}}
      />
    </div>
  );
}

export default ZoneVolumeSlider;
