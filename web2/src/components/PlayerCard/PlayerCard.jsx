import Card from "@/components/Card/Card";
import "./PlayerCard.scss";
import StreamBadge from "@/components/StreamBadge/StreamBadge";
import SongInfo from "../SongInfo/SongInfo";
import VolumeSlider from "../VolumeSlider/VolumeSlider";
import { useState, useEffect } from "react";
import PlayerImage from "../PlayerImage/PlayerImage";
import ZonesBadge from "../ZonesBadge/ZonesBadge";

const UPDATE_INTERVAL = 1000;

const PlayerCard = ({ source_id, info, zones, vol, setVol }) => {
  return (
    <Card>
      <div className="outer">
        <div className="content">
          <ZonesBadge zones={zones} />
        </div>
        <div className="content stream-name-container">
          <StreamBadge info={info}/>
        </div>
        <div className="content">
          <PlayerImage info={info} className="album-art"/>
        </div>
        <div className="content">
          <SongInfo info={info}/>
        </div>
        <div className="content vol">
          <VolumeSlider
            vol={vol}
            onChange={(event, vol)=>{setVol(source_id, event, vol)}}
          />
        </div>
      </div>
    </Card>
  );
};

export default PlayerCard
