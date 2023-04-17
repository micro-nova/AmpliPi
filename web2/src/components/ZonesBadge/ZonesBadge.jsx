import './ZonesBadge.scss';
import { useState, useEffect } from 'react';
import { getSourceZones } from "@/pages/Home/Home.jsx"
import { useStatusStore } from '@/App.jsx'
import { chipClasses } from '@mui/material';

const ZoneChip = ({ zone }) => {
  return (
    <div className='zone-chip'>
      <div className='zone-text'>
        {zone.name}
      </div>
    </div>
  )
}

const ZonesBadge = ({ sourceId }) => {
  const allZones = useStatusStore((s) => s.status.zones)
  const usedZones = getSourceZones(sourceId, allZones)


  let chips = [];

  switch (usedZones.length) {
    case 0:
      chips.push(<ZoneChip key={0} zone={{ name: 'Add Zones' }} />)
      break
    case 1:
      chips.push(<ZoneChip key={0} zone={usedZones[0]} />)
      break
    case 2:
      chips.push(<ZoneChip key={0} zone={usedZones[0]} />)
      chips.push(<ZoneChip key={1} zone={usedZones[1]} />)
      break
    default:
      chips.push(<ZoneChip key={0} zone={usedZones[0]} />)
      chips.push(<ZoneChip key={1} zone={{ name: `+${usedZones.length - 2} more` }} />)
  }

  return <div>{chips}</div>
}

export default ZonesBadge
