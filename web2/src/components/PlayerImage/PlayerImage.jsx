import './PlayerImage.scss';
import { useState, useEffect } from 'react';

const UPDATE_INTERVAL = 1000

const PlayerImage = ({ getInfo, className }) => {
  const [pic, setPic] = useState('')

  return  (
    useEffect(() => {
      const interval = setInterval(() => {
        setPic(getInfo().img_url)
      }, UPDATE_INTERVAL)
      return () => clearInterval(interval)
    }, []),

    <img src={pic} className={`image ${className}`}/>

    )

}

export default PlayerImage
