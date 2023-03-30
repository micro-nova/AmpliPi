import './SongInfo.scss'
import { useState, useEffect } from 'react'

const UPDATE_INTERVAL = 1000

const SongInfo = ({ getInfo }) => {

  const [info, setInfo] = useState({})

  return (
    useEffect(() => {
      const interval = setInterval(() => {
        setInfo(getInfo())
      }, UPDATE_INTERVAL)
      return () => clearInterval(interval)
    }, []),

    <div className="song-info">
      <h3>{info.artist}</h3>
      <h4>{info.album}</h4>
      <h3>{info.track}</h3>
    </div>
  );
}

export default SongInfo;
