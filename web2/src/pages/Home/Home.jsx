import PlayerCard from "@/components/PlayerCard/PlayerCard";
import "./Home.scss";
import { useStatusStore } from '@/App.jsx'
import ZonesModal from "@/components/ZonesModal/ZonesModal";
import StreamsModal from "@/components/StreamsModal/StreamsModal";
import { useState } from "react";

export const getSourceZones = (source_id, zones) => {
  let matches = [];
  for (const i of zones) {
    if (i.source_id == source_id) {
      matches.push(i);
    }
  }
  return matches;
};

const Home = ({ selectedSource, setSelectedSource }) => {
  const sources = useStatusStore((s)=>s.status.sources)
  const clearSourceZones = useStatusStore((s)=>s.clearSourceZones)
  const [zonesModalOpen, setZonesModalOpen] = useState(false)
  const [streamsModalOpen, setStreamsModalOpen] = useState(false)
  let playerCards = [];
  let nextAvailableSource = null;

  sources.forEach((source, i) => {
    if(source.input.toUpperCase() != "NONE" && source.input != ""){
      playerCards.push(
        <PlayerCard
          key={i}
          sourceId={source.id}
          selectedSource={selectedSource}
          setSelectedSource={setSelectedSource}
        />
      )
      } else {
        nextAvailableSource = source.id;
      }
  })

  const initSource = (sourceId) => {
    // clear source zones
    clearSourceZones(sourceId)

    // open first modal
    setZonesModalOpen(true)
  }

  return (
    <div className="home-outer">
      <div className="home-view">
        {/* <PlayerCard
          sourceId={0}
          selectedSource={selectedSource}
          setSelectedSource={setSelectedSource}
        />
        <PlayerCard
          sourceId={1}
          selectedSource={selectedSource}
          setSelectedSource={setSelectedSource}
        />
        <PlayerCard
          sourceId={2}
          selectedSource={selectedSource}
          setSelectedSource={setSelectedSource}
        />
        <PlayerCard
          sourceId={3}
          selectedSource={selectedSource}
          setSelectedSource={setSelectedSource}
        /> */}

        {
          playerCards
        }

        {playerCards.length < sources.length &&
          <div className="home-add-player-button" onClick={()=>{initSource(nextAvailableSource)}}>+</div>
        }
      </div>

      {zonesModalOpen && <ZonesModal sourceId={nextAvailableSource} setZoneModalOpen={(o)=>{setStreamsModalOpen(!o); setZonesModalOpen(o)}} onClose={()=>setZonesModalOpen(false)}/>}
      {streamsModalOpen && <StreamsModal sourceId={nextAvailableSource} setStreamModalOpen={(o)=>setStreamsModalOpen(o)} onClose={()=>setStreamsModalOpen(false)}/>}

    </div>

  );
};

export default Home;
