import Card from "@/components/Card/Card";
import "./PlayerCard.scss";
import StreamBadge from "@/components/StreamBadge/StreamBadge";
import SongInfo from "../SongInfo/SongInfo";
import VolumeSlider from "../VolumeSlider/VolumeSlider";
import { useState, useEffect } from "react";
import PlayerImage from "../PlayerImage/PlayerImage";
import ZonesBadge from "../ZonesBadge/ZonesBadge";

const PlayerCard = ({ source_id, getInfo, getZones, getPlayerVol, setPlayerVol }) => {

  return (
    <Card>
      <div className="outer">
        <div className="content">
          <ZonesBadge getZones={getZones} />
        </div>
        <div className="content stream-name-container">
          <StreamBadge getInfo={getInfo}/>
        </div>
        <div className="content">
          <PlayerImage getInfo={getInfo} className="album-art"/>
        </div>
        <div className="content">
          <SongInfo getInfo={getInfo}/>
        </div>
        <div className="content vol">
          <VolumeSlider
            getValue={()=>{return getPlayerVol(source_id)}}
            onChange={(event, vol)=>{setPlayerVol(source_id, event, vol)}}
          />
        </div>
      </div>
    </Card>
  );
};

export default PlayerCard
