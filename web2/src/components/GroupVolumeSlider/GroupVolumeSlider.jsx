import Slider from "@mui/material/Slider";
import { useState, useEffect } from "react";
import './GroupVolumeSlider.scss'
import { getSourceZones } from "@/pages/Home/Home"
import { useStatusStore } from "@/App"
import ZoneVolumeSlider from "../ZoneVolumeSlider/ZoneVolumeSlider";
import { IconButton } from '@mui/material'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

let sendingRequestCount = 0

const GroupVolumeSlider = ({groupId}) => {
  const volume = useStatusStore((s) => s.status.groups.filter((g) => g.id === groupId)[0].vol_f)
  const setGroupVol = useStatusStore((s) => s.setGroupVol)
  const group = useStatusStore((s) => s.status.groups.filter((g) => g.id === groupId)[0])
  const [slidersOpen, setSlidersOpen] = useState(false)
  const zones = []

  for(const zoneId of group.zones) {
    zones.push(<ZoneVolumeSlider key={zoneId} zoneId={zoneId} />)
  }
  const setVol = (vol) => {
    if(sendingRequestCount <= 0) {
      sendingRequestCount += 1
      fetch(`/api/groups/${groupId}`, {
        method: 'PATCH',
        headers: {
          'Content-type': 'application/json',
        },
        body: JSON.stringify({vol_f: vol}),
      }).then(() => {sendingRequestCount -= 1})
    }
  }

  return (
    <div className="group-volume-container">
      {group.name[0].toUpperCase() + group.name.slice(1)}
      <div className="group-zones-container">
        <Slider
          min={0}
          step={0.01}
          max={1}
          value={volume}
          onChange={(e, val) => {setGroupVol(groupId, val); setVol(val)}}
        />

        <IconButton onClick={()=>setSlidersOpen(!slidersOpen)}>
          {
            slidersOpen ? <KeyboardArrowUpIcon className='groups-slider-expand-button' style={{width:"3rem", height:"3rem"}}/> :
            <KeyboardArrowDownIcon className='groups-slider-expand-button' style={{width:"3rem", height:"3rem"}}/>
          }
        </IconButton>
      </div>
      {slidersOpen && <div className="group-volume-children-container">
        {zones}
      </div>}
    </div>
  );
}

export default GroupVolumeSlider;