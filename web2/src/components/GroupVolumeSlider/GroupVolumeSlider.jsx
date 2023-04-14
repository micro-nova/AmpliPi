import Slider from "@mui/material/Slider";
import { useState, useEffect } from "react";
import './GroupVolumeSlider.scss'
import { getSourceZones } from "@/pages/Home/Home"
import { useStatusStore } from "@/App"
import ZoneVolumeSlider from "../ZoneVolumeSlider/ZoneVolumeSlider";
import { IconButton } from '@mui/material'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import VolumeSlider from "../VolumeSlider/VolumeSlider";

let sendingRequestCount = 0

const GroupVolumeSlider = ({groupId}) => {
  const volume = useStatusStore((s) => s.status.groups.filter((g) => g.id === groupId)[0].vol_f)
  const setGroupVol = useStatusStore((s) => s.setGroupVol)
  const setGroupMute = useStatusStore((s) => s.setGroupMute)
  const group = useStatusStore((s) => s.status.groups.filter((g) => g.id === groupId)[0])
  const [slidersOpen, setSlidersOpen] = useState(false)
  const zones = []

  for(const zoneId of group.zones) {
    zones.push(<ZoneVolumeSlider key={zoneId} zoneId={zoneId} />)
  }
  const setVol = (vol) => {

    setGroupVol(groupId, vol)

    if(sendingRequestCount <= 0) {
      sendingRequestCount += 1
      fetch(`/api/groups/${groupId}`, {
        method: 'PATCH',
        headers: {
          'Content-type': 'application/json',
        },
        body: JSON.stringify({vol_f: vol, mute: false}),
      }).then(() => {sendingRequestCount -= 1})
    }
  }

  const setMute = (mute) => {
    setGroupMute(groupId, mute)

    fetch(`/api/groups/${groupId}`, {
      method: 'PATCH',
      headers: {
        'Content-type': 'application/json',
      },
      body: JSON.stringify({mute: mute}),
    })
  }


  return (
    <div className="group-volume-container">
      {group.name[0].toUpperCase() + group.name.slice(1)}
      <div className="group-zones-container">

        <VolumeSlider mute={group.mute} setMute={setMute} vol={volume} setVol={setVol} />

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
