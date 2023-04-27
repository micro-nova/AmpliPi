import "./ZonesBadge.scss"
import { getSourceZones } from "@/pages/Home/Home.jsx"
import { useStatusStore } from "@/App.jsx"
import Chip from "../Chip/Chip"

const ZoneChip = ({ zone, onClick }) => {
  return (
    <Chip onClick={onClick}>
      <div className="zone-text">{zone.name}</div>
    </Chip>
  )
}

const ZonesBadge = ({ sourceId, onClick }) => {
  const allZones = useStatusStore((s) => s.status.zones)
  const usedZones = getSourceZones(sourceId, allZones)

  let chips = []


  switch (usedZones.length) {
    case 0:
      chips.push(<ZoneChip key={0} onClick={onClick} zone={{ name: "Add Zones" }} />)
      break
    case 1:
      chips.push(<ZoneChip key={0} onClick={onClick} zone={usedZones[0]} />)
      break
    case 2:
      chips.push(<ZoneChip key={0} onClick={onClick} zone={usedZones[0]} />)
      chips.push(<ZoneChip key={1} onClick={onClick} zone={usedZones[1]} />)
      break
    default:
      chips.push(<ZoneChip key={0} onClick={onClick} zone={usedZones[0]} />)
      chips.push(
        <ZoneChip key={1} onClick={onClick} zone={{ name: `+${usedZones.length - 2} more` }} />
      )
  }

  return <div>{chips}</div>
  
}

export default ZonesBadge
