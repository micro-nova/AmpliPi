import Card from "@/components/Card/Card";
import "./PlayerCard.scss";
import StreamBadge from "@/components/StreamBadge/StreamBadge";
import SongInfo from "../SongInfo/SongInfo";
import VolumeSlider from "../VolumeSlider/VolumeSlider";
import { useState, useEffect } from "react";
import PlayerImage from "../PlayerImage/PlayerImage";
import ZonesBadge from "../ZonesBadge/ZonesBadge";

const PlayerCard = ({ sourceId, info, zones, vol, setVol, selectedId, setSelectedId }) => {
  const selected = selectedId === sourceId

  const select = () => {
    setSelectedId(sourceId)
  }

  return (
    <Card selected={selected}>
      <div className="outer">
        <div className="content">
          <ZonesBadge zones={zones} />
        </div>
        <div className="content stream-name-container">
          <StreamBadge info={info} />
        </div>
        <div className="content album-art" onClick={select}>
          <div>
            <PlayerImage info={info} />
          </div>
          
        </div>
        <div className="content" onClick={select}>
          <SongInfo info={info} />
        </div>
        <div className="content vol">
          <VolumeSlider
            vol={vol}
            onChange={(event, vol)=>{setVol(sourceId, event, vol)}}
          />
        </div>
      </div>
    </Card>
  );
};

export default PlayerCard
