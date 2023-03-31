import './SongInfo.scss'
import { useState, useEffect } from 'react'

const SongInfo = ({ info }) => {

  return (
    <div className="song-info">
      <div className="artist-name">{info.artist}</div>
      <div className="album-name">{info.album}</div>
      <div className="track-name">{info.track}</div>
    </div>
  );
}

export default SongInfo;
