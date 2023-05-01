import "./ZonesBadge.scss"
import { getSourceZones } from "@/pages/Home/Home.jsx"
import { useStatusStore } from "@/App.jsx"
import Chip from "../Chip/Chip"
import { getFittestRep } from "@/utils/GroupZoneFiltering"

const ZoneGroupChip = ({ zoneGroup, onClick }) => {
  return (
    <Chip onClick={onClick}>
      <div className="zone-text">{zoneGroup.name}</div>
    </Chip>
  )
}

const ZonesBadge = ({ sourceId, onClick }) => {
  const zones = getSourceZones(sourceId, useStatusStore(s => s.status.zones))
  const groups = getSourceZones(sourceId, useStatusStore(s => s.status.groups))

  // compute the best representation of the zones and groups
  const {zones: bestZones, groups: bestGroups} = getFittestRep(zones, groups)

  const combined = [...bestGroups, ...bestZones]

  let chips = []
  switch (combined.length) {
    case 0:
      chips.push(<ZoneGroupChip key={0} onClick={onClick} zoneGroup={{ name: "Add Zones" }} />)
      break
    case 1:
      chips.push(<ZoneGroupChip key={0} onClick={onClick} zoneGroup={combined[0]} />)
      break
    case 2:
      chips.push(<ZoneGroupChip key={0} onClick={onClick} zoneGroup={combined[0]} />)
      chips.push(<ZoneGroupChip key={1} onClick={onClick} zoneGroup={combined[1]} />)
      break
    default:
      chips.push(<ZoneGroupChip key={0} onClick={onClick} zoneGroup={combined[0]} />)
      chips.push(
        <ZoneGroupChip key={1} onClick={onClick} zoneGroup={{ name: `+${combined.length - 1} more` }} />
      )
  }

  return <div>{chips}</div>

}

export default ZonesBadge
