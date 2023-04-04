import Card from "@/components/Card/Card";
import "./PlayerCard.scss";
import StreamBadge from "@/components/StreamBadge/StreamBadge";
import SongInfo from "../SongInfo/SongInfo";
import VolumeSlider from "../VolumeSlider/VolumeSlider";
import { useState, useEffect } from "react";
import PlayerImage from "../PlayerImage/PlayerImage";
import ZonesBadge from "../ZonesBadge/ZonesBadge";
import StreamsModal from "../StreamsModal/StreamsModal";
import ZonesModal from "../ZonesModal/ZonesModal";

const PlayerCard = ({ sourceId, info, zones, usedZones, vol, setVol, selectedSource, setSelectedSource, streams }) => {
  const [StreamModalOpen, setStreamModalOpen] = useState(false);
  const [ZoneModalOpen, setZoneModalOpen] = useState(false);
  const selected = selectedSource === sourceId

  const select = () => {
    setSelectedSource(sourceId)
  }

  const setStream = (streamId) => {
    setStreamModalOpen(false)
    setSelectedSource(sourceId)

    fetch(`/api/sources/${sourceId}`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({ input: `stream=${streamId}` }),
    });
  }

  const setZones = (zoneIds) => {
    let removeList = []

    setZoneModalOpen(false)
    setSelectedSource(sourceId)

    for(const zone of usedZones){
      if(!zoneIds.includes(zone.id)){
        removeList.push(zone.id)
      }
    }

    fetch(`/api/zones`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({ zones: removeList, update:{source_id:-1} }),
    });

    fetch(`/api/zones`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({ zones: zoneIds, update:{mute: false, source_id:sourceId} }),
    });
  }

  return (
    <Card selected={selected}>
      <div className="outer">
        <div className="content" onClick={()=>{setZoneModalOpen(true)}}>
          <ZonesBadge zones={usedZones} />
        </div>
        <div className="content stream-name-container" onClick={()=>{setStreamModalOpen(true)}}>
          <StreamBadge name={info.name.split(" - ")[0]} type={info.name.split(" - ")[1]} />
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
       {StreamModalOpen && <StreamsModal streams={streams} setStream={setStream}/>}
       {ZoneModalOpen && <ZonesModal groups={groups} zones={zones} setZones={setZones} sourceId={sourceId}/>}
      </div>
    </Card>
  );
};

export default PlayerCard
