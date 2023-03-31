import './ZonesBadge.scss';
import { useState, useEffect } from 'react';

const ZonesBadge = ({ zones }) => {
  let zones_text = ''
  if(zones.length > 2) {
    zones_text = `${zones[0].name} and ${zones.length - 1} more`
  } else if(zones.length == 2) {
    zones_text = `${zones[0].name} and ${zones[1].name}`
  } else if(zones.length == 1) {
    zones_text = `${zones[0].name}`
  }

  return (
    <div className='zone-text'>
      {zones_text}
    </div>
  );
}

export default ZonesBadge;
