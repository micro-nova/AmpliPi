import './PlayerImage.scss';
import { useState, useEffect } from 'react';

const PlayerImage = ({ info, className }) => {

  return  (
    <img src={info.img_url} className={`image ${className}`}/>
    )

}

export default PlayerImage
