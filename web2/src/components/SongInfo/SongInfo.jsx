import './SongInfo.scss'
import { useState, useEffect } from 'react'

const UPDATE_INTERVAL = 1000

const SongInfo = ({ info }) => {

  return (
    <div className="song-info">
      <h3>{info.artist}</h3>
      <h4>{info.album}</h4>
      <h3>{info.track}</h3>
    </div>
  );
}

export default SongInfo;
