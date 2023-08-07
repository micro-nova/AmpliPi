import './VolumesDrawer.scss'
import { useStatusStore } from '@/App.jsx'
import { Drawer } from '@mui/material';
import { getSourceZones } from '@/pages/Home/Home'
import ZoneVolumeSlider from '../ZoneVolumeSlider/ZoneVolumeSlider';
import GroupVolumeSlider from '../GroupVolumeSlider/GroupVolumeSlider';

// container for volume sliders on player page
const VolumesDrawer = ({ open, onClose, sourceId }) => {
  const zones = getSourceZones(sourceId, useStatusStore.getState().status.zones)
  const groups = getSourceZones(sourceId, useStatusStore.getState().status.groups)

  const ZoneVolumeSliders = []
  const GroupVolumeSliders = []

  for (const group of groups) {
    if (group.source_id == sourceId) {
      GroupVolumeSliders.push(
          <GroupVolumeSlider key={group.id} groupId={group.id}/>
      )
    }
  }

  for (const zone of zones) {
    let grouped = false

    for (const group of groups) {
      if (group.zones.includes(zone.id)) {
        grouped = true
      }
    }
    if(!grouped){
      ZoneVolumeSliders.push(<ZoneVolumeSlider key={zone.id} zoneId={zone.id} />)
    }
  }

  return(
    <Drawer
    open={open}
    onClose={()=>onClose()}
    anchor="bottom"
    >
      <div className='volume-sliders-container'>
        {
          GroupVolumeSliders
        }
        {
          ZoneVolumeSliders
        }
      </div>

    </Drawer>
  )
}

export default VolumesDrawer
