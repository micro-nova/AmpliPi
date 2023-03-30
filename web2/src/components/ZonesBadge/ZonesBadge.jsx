import './ZonesBadge.scss';
import { useState, useEffect } from 'react';

const UPDATE_INTERVAL = 1000

const ZonesBadge = ({ getZones }) => {
  const [zones, setZones] = useState([]);

  let zones_text = ''
  if(zones.length > 2) {
    zones_text = `${zones[0].name} and ${zones.length - 1} more`
  } else if(zones.length == 2) {
    zones_text = `${zones[0].name} and ${zones[1].name}`
  } else if(zones.length == 1) {
    zones_text = `${zones[0].name}`
  }

  return (
    useEffect(() => {
      const interval = setInterval(() => {
        setZones(getZones());
      }, UPDATE_INTERVAL);
      return () => clearInterval(interval);
    }, []),

    <div className='zones-text'>
      {zones_text}
    </div>
  );
}

export default ZonesBadge;
