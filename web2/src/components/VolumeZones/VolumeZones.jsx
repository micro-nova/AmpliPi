import "./VolumesZones.scss"
import { useStatusStore } from "@/App.jsx"
import { getSourceZones } from "@/pages/Home/Home"
import ZoneVolumeSlider from "../ZoneVolumeSlider/ZoneVolumeSlider"
import GroupVolumeSlider from "../GroupVolumeSlider/GroupVolumeSlider"
import Card from "../Card/Card"

const groupZoneMatchCount = (zones, group) => zones.reduce((sum, zone) => sum + group.zones.includes(zone.id) ? 1 : 0, 0)

// returns the group with the most matches, and updated zones and groups
const getFittestGroup = (zones, groups) => {
  let bestFitness = 0
  let best = null
  for (const group of groups) {
    let fitness = groupZoneMatchCount(zones, group)
    if (fitness > bestFitness) {
      bestFitness = fitness
      best = group
    }
  }

  let newZones = zones
  let newGroups = groups

  if (best !== null) {
    newZones = zones.filter(zone => !best.zones.includes(zone.id))
    newGroups = groups.filter(group => group !== best)
  }

  return {
    'best': best,
    'zones': newZones,
    'groups': newGroups,
  }
}



const VolumeZones = ({ sourceId }) => {
  const zones = getSourceZones(sourceId, useStatusStore.getState().status.zones)
  const groups = getSourceZones( 
    sourceId,
    useStatusStore.getState().status.groups
  )

  const ZoneVolumeSliders = []
  const GroupVolumeSliders = []

  for (const group of groups) {
    GroupVolumeSliders.push(
      <Card className="group-vol-card" key={group.id}>
        <GroupVolumeSlider groupId={group.id} />
      </Card>
    )
  }

  for (const zone of zones) {
    let grouped = false

    for (const group of groups) {
      if (group.zones.includes(zone.id)) {
        grouped = true
      }
    }
    if (!grouped) {
      ZoneVolumeSliders.push(
        <Card className="zone-vol-card" key={zone.id}>
          <ZoneVolumeSlider zoneId={zone.id} />
        </Card>
      )
    }
  }

  return (
    <div className="volume-sliders-container">
      {GroupVolumeSliders}
      {ZoneVolumeSliders}
    </div>
  )
}

export default VolumeZones
