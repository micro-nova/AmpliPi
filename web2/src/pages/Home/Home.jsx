import PlayerCard from "@/components/PlayerCard/PlayerCard";
import "./Home.scss";

const Home = ({ status, selectedId, setSelectedId }) => {
  const sources = status.sources;
  const zones = status.zones;

  const getSourceZones = (source_id) => {
    let matches = [];
    for (const i of zones) {
      if (i.source_id == source_id) {
        matches.push(i);
      }
    }
    return matches;
  };

  const setPlayerVol = (source_id, event, vol) => {
    // console.log(`setting vol to ${vol}`)
    let delta = vol - getPlayerVol(source_id);

    for (const i of getSourceZones(source_id)) {
      let set_pt = 0;
      if (i.vol_f + delta <= 1 && i.vol_f + delta >= 0) {
        set_pt = i.vol_f + delta;
      }
      set_pt = Math.max(0, Math.min(1, set_pt));
      // console.log(`setting zone ${i.name} to ${set_pt}`)
      i.vol_f = set_pt;
      fetch(`/api/zones/${i.id}`, {
        method: "PATCH",
        headers: {
          "Content-type": "application/json",
        },
        body: JSON.stringify({ vol_f: set_pt }),
      });
    }
  };

  const getPlayerVol = (source_id) => {
    let vol = 0;
    let n = 0;
    for (const i of getSourceZones(source_id)) {
      n += 1;
      vol += i.vol_f;
    }

    const avg = vol / n;

    if (isNaN(avg)) {
      return 0;
    } else {
      // console.log(`returning ${avg}`)
      return avg;
    }
  };

  return (
    <div className="home-outer">
      <div className="home-view">
        <PlayerCard
          sourceId={0}
          info={sources[0].info}
          zones={getSourceZones(0)}
          vol={getPlayerVol(0)}
          setVol={setPlayerVol}
          selectedId={selectedId}
          setSelectedId={setSelectedId}
        />
        <PlayerCard
          sourceId={1}
          info={sources[1].info}
          zones={getSourceZones(1)}
          vol={getPlayerVol(1)}
          setVol={setPlayerVol}
          selectedId={selectedId}
          setSelectedId={setSelectedId}
        />
        <PlayerCard
          sourceId={2}
          info={sources[2].info}
          zones={getSourceZones(2)}
          vol={getPlayerVol(2)}
          setVol={setPlayerVol}
          selectedId={selectedId}
          setSelectedId={setSelectedId}
        />
        <PlayerCard
          sourceId={3}
          info={sources[3].info}
          zones={getSourceZones(3)}
          vol={getPlayerVol(3)}
          setVol={setPlayerVol}
          selectedId={selectedId}
          setSelectedId={setSelectedId}
        />
      </div>
    </div>

  );
};

export default Home;
