import PlayerCard from "@/components/PlayerCard/PlayerCard";
import "./Home.scss";

const UPDATE_INTERVAL = 500;

const Home = ({getSources, getZones}) => {


  const getSourceZones = (source_id) =>{
    let zones = [];
    for(const i of getZones()){
      if(i.source_id == source_id){
        zones.push(i);
      }
    }
    return zones;
  }

  const setPlayerVol = (source_id, event, vol) => {
    console.log(`setting vol to ${vol}`)
    let delta = vol - getPlayerVol(source_id);

    for(const i of getSourceZones(source_id)){
        let set_pt = 0;
        if(i.vol_f + delta <= 1 && i.vol_f + delta >= 0){
          set_pt = i.vol_f + delta;
        }
        set_pt = Math.max(0, Math.min(1, set_pt))
        console.log(`setting zone ${i.name} to ${set_pt}`)
        i.vol_f = set_pt;
        fetch(`/api/zones/${i.id}`, {method: 'PATCH', headers: {
          'Content-type': 'application/json',
        }, body: JSON.stringify({vol_f: set_pt})})

    }
  }

  const getPlayerVol = (source_id) => {
    let vol = 0;
    let n = 0;
    for(const i of getSourceZones(source_id)){
        n += 1;
        vol += i.vol_f;
    }

    const avg = vol/n;

    if(isNaN(avg)){
      return 0;
    } else {
      // console.log(`returning ${avg}`)
      return avg;
    }
  }

  return (
    <div className="home-view">
      <PlayerCard source_id={0} getInfo={()=>{return getSources()[0].info}} getZones={()=>{return getSourceZones(0)}} getPlayerVol={getPlayerVol} setPlayerVol={setPlayerVol} />
      <PlayerCard source_id={1} getInfo={()=>{return getSources()[1].info}} getZones={()=>{return getSourceZones(1)}} getPlayerVol={getPlayerVol} setPlayerVol={setPlayerVol} />
      <PlayerCard source_id={2} getInfo={()=>{return getSources()[2].info}} getZones={()=>{return getSourceZones(2)}} getPlayerVol={getPlayerVol} setPlayerVol={setPlayerVol} />
      <PlayerCard source_id={3} getInfo={()=>{return getSources()[3].info}} getZones={()=>{return getSourceZones(3)}} getPlayerVol={getPlayerVol} setPlayerVol={setPlayerVol} />
    </div>
  );
}

export default Home
