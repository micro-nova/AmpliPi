import { useEffect, useState } from "react";
import { create } from 'zustand';
import { useCookies } from 'react-cookie';
import "@/App.scss";
import Home from "@/pages/Home/Home";
import Player from "@/pages/Player/Player";
import MenuBar from "./components/MenuBar/MenuBar";
import produce from 'immer'
import { getSourceZones } from "@/pages/Home/Home"
import { applyPlayerVol } from "./components/VolumeSlider/VolumeSlider"

const UPDATE_INTERVAL = 1000;


export const useStatusStore = create((set) => ({
  status: null,
  setZonesVol: (vol, zones, sourceId) => {
    set(produce((s) => {
      applyPlayerVol(vol, zones, sourceId, (zone_id, new_vol) => {
        // let zone = null
        // for (const z of s.status.zones) {
        //   if (z.id === zone_id) {
        //     zone = z;
        //     s.status.zones
        //   }
        // }

        for (const i in s.status.zones) {
          if (s.status.zones[i].id === zone_id) {
            s.status.zones[i].vol_f = new_vol
          }
        }

        // zone.vol_f = new_vol
      })
    }))
  },
  fetch: async () => {
    const res = await fetch(`/api`)
    set({ status: await res.json() })
  },
  setZoneVol: (zoneId, new_vol) => {
    set(produce((s) => {
      s.status.zones[zoneId].vol_f = new_vol
    }))
  },
  setGroupVol: (groupId, new_vol) => {
    set(produce((s) => {
      let g = s.status.groups.filter((g) => g.id === groupId)[0]
      for (const i of g.zones) {
        s.status.zones[i].vol_f = new_vol
      }
      g.vol_f = new_vol
    }))
  }

}))

function App() {
  const [selectedSource, setSelectedSource] = useState(0);
  const [selectedPage, setSelectedPage] = useState(0);
  const [isLoaded, setIsLoaded] = useState(false);

  const update = useStatusStore((s) => s.fetch)

  if (isLoaded == false) {

    return (
      useEffect(() => {
        const interval = setInterval(() => {
          update().then(() => setIsLoaded(true));
        }, UPDATE_INTERVAL);
        return () => clearInterval(interval);
      }, []),
      (<h1>Loading...</h1>)
    );


  }

  const Page = () => {
      switch(selectedPage) {
      default:
        return <Home selectedSource={selectedSource} setSelectedSource={setSelectedSource} />
      case 1:
        return <Player selectedSource={selectedSource} />
      case 2:
        return <div></div>
      case 3:
        return <div></div>
    }
  }

  return (
    useEffect(() => {
      update();
      const interval = setInterval(() => {
        update();
      }, UPDATE_INTERVAL);
      return () => clearInterval(interval);
    }, []),
    (
      <div className="app">
        <div style={{paddingBottom: '56px'}}>
          <Page />
        </div>
        <MenuBar pageNumber={selectedPage} onChange={(n)=>{console.log(`changing page to ${n}`); setSelectedPage(n)}}/>
      </div>
    )
  );
}

export default App;
