import "./ZonesBadge.scss"
import { getSourceZones } from "@/pages/Home/Home.jsx"
import { useStatusStore } from "@/App.jsx"
import Chip from "../Chip/Chip"
import { getFittestRep } from "@/utils/GroupZoneFiltering"
import { useState, useEffect } from 'react'

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
  // switch (combined.length) {
  //   case 0:
  //     chips.push(<ZoneGroupChip key={0} onClick={onClick} zoneGroup={{ name: "Add Zones" }} />)
  //     break
  //   case 1:
  //     chips.push(<ZoneGroupChip key={0} onClick={onClick} zoneGroup={combined[0]} />)
  //     break
  //   case 2:
  //     chips.push(<ZoneGroupChip key={0} onClick={onClick} zoneGroup={combined[0]} />)
  //     chips.push(<ZoneGroupChip key={1} onClick={onClick} zoneGroup={combined[1]} />)
  //     break
  //   default:
  //     chips.push(<ZoneGroupChip key={0} onClick={onClick} zoneGroup={combined[0]} />)
  //     chips.push(
  //       <ZoneGroupChip key={1} onClick={onClick} zoneGroup={{ name: `+${combined.length - 1} more` }} />
  //     )
  // }

  // TODO: cleanup. or maybe even just get rid of this resize logic.
  // only does anything on desktop, and we are going to have a
  // custom desktop version anyway so this will be unnecessary
  // in the future.
  function getWindowDimensions() {
    const { innerWidth: width, innerHeight: height } = window;
    return {
      width,
      height
    };
  }

  const [windowDimensions, setWindowDimensions] = useState(getWindowDimensions());

  useEffect(() => {
    function handleResize() {
      setWindowDimensions(getWindowDimensions());
    }

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const { width, height } = windowDimensions
  const amount = 2 + Math.max(2 * Math.floor((width - 550) / 220), 0)


  if (combined.length >= amount) {
    for (let i = 0; i < amount-1; i++) {
      const item = combined[i]
      chips.push(<ZoneGroupChip key={i} onClick={onClick} zoneGroup={item} />)
    }
    chips.push(<ZoneGroupChip key={1} onClick={onClick} zoneGroup={{ name: `+${combined.length - (amount-1)} more` }} />)
  } else if (combined.length > 0) {
    for (const [i, item] of combined.entries()) {
      chips.push(<ZoneGroupChip key={i} onClick={onClick} zoneGroup={item} />)
    }
  } else {
    chips.push(<ZoneGroupChip key={0} onClick={onClick} zoneGroup={{ name: "Add Zones" }} />)
  }

  return <div className="zones-container">{chips}</div>
}

export default ZonesBadge
