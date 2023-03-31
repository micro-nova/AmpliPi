import './StreamBadge.scss'
import spotify from '@/assets/spotify.png'
import { useState, useEffect } from 'react'

const UPDATE_INTERVAL = 1000

const StreamBadge = ({ info }) => {
  info = info.name.split(" - ")
  const name = info[0]
  const type = info[1]

  const icon = spotify
  //TODO: populate this with icons or add endpoint to get icons
  switch (type) {
  }

  return (
    <div className="stream-badge">
      <div className="stream-name">
      {name}
      </div>
        <img src={icon} className="stream-icon" alt="stream icon" />
    </div>
  );
}

export default StreamBadge
