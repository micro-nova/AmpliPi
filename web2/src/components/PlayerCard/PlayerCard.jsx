import Card from "@/components/Card/Card";
import "./PlayerCard.scss";
import StreamBadge from "@/components/StreamBadge/StreamBadge";
import SongInfo from "../SongInfo/SongInfo";
import CardVolumeSlider from "../CardVolumeSlider/CardVolumeSlider";
import { useState, useEffect } from "react";
import PlayerImage from "../PlayerImage/PlayerImage";
import ZonesBadge from "../ZonesBadge/ZonesBadge";
import StreamsModal from "../StreamsModal/StreamsModal";
import ZonesModal from "../ZonesModal/ZonesModal";

const PlayerCard = ({ sourceId, selectedSource, setSelectedSource }) => {
  const [streamModalOpen, setStreamModalOpen] = useState(false);
  const [zoneModalOpen, setZoneModalOpen] = useState(false);
  const selected = selectedSource === sourceId

  return (
    <Card selected={selected}>
      <div className="outer">
        <div className="content" onClick={()=>{setZoneModalOpen(true)}}>
          <ZonesBadge sourceId={sourceId}/>
        </div>
        <div className="content stream-name-container" onClick={()=>{setStreamModalOpen(true)}}>
          <StreamBadge sourceId={sourceId} />
        </div>
        <div className="content album-art" onClick={() => setSelectedSource(sourceId)}>
          <div>
            <PlayerImage sourceId={sourceId} />
          </div>
        </div>
        <div className="content" onClick={() => setSelectedSource(sourceId)}>
          <SongInfo sourceId={sourceId} />
        </div>
        <div className="content vol">
          <CardVolumeSlider
            sourceId={sourceId}
            onChange={(event, vol)=>{setVol(sourceId, event, vol)}}
          />
        </div>
       {streamModalOpen && <StreamsModal sourceId={sourceId} setStreamModalOpen={setStreamModalOpen} onClose={()=>setStreamModalOpen(false)}/>}
       {zoneModalOpen && <ZonesModal sourceId={sourceId} setZoneModalOpen={setZoneModalOpen} onClose={()=>setZoneModalOpen(false)}/>}
      </div>
    </Card>
  );
};

export default PlayerCard
