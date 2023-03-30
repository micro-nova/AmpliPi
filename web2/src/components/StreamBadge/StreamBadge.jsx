import './StreamBadge.scss'
import spotify from '@/assets/spotify.png'
import { useState, useEffect } from 'react'

const UPDATE_INTERVAL = 1000

const StreamBadge = ({ getInfo }) => {
  const [name, setName] = useState('')
  const [type, setType] = useState('')

  const icon = spotify
  //TODO: populate this with icons or add endpoint to get icons
  switch (type) {
  }

  return (
    useEffect(() => {
      const interval = setInterval(() => {
        const fullname = getInfo().name.split(' - ')
        setName(fullname[0])
        setType(fullname[1])
      }, UPDATE_INTERVAL)
      return () => clearInterval(interval)
    }, []),

    <div className="stream-badge">
      <div className="stream-name">
      {name}
      </div>
        <img src={icon} className="stream-icon" alt="stream icon" />
    </div>
  );
}

export default StreamBadge
