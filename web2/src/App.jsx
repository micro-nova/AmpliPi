import spotify from '@/assets/spotify.png'
import dlna from '@/assets/dlna.png'
import bluetooth from '@/assets/bluetooth.png'
import fmradio from '@/assets/fmradio.png'
import shairport from '@/assets/shairport.png'
import pandora from '@/assets/pandora.png'
import plexamp from '@/assets/plexamp.png'
import lms from '@/assets/lms.png'
import internetradio from '@/assets/internet_radio.png'
import rca from '@/assets/rca_inputs.jpg'
import { useEffect, useState } from "react";
import { create } from 'zustand';
import "@/App.scss";
import Home from "@/pages/Home/Home";
import Player from "@/pages/Player/Player";
import MenuBar from "./components/MenuBar/MenuBar";
import Settings from "@/pages/Settings/Settings";
import produce from 'immer'
import { getSourceZones } from "@/pages/Home/Home"
import { applyPlayerVol } from "./components/CardVolumeSlider/CardVolumeSlider"
import { router } from "@/main"

const UPDATE_INTERVAL = 1000;

export const useStatusStore = create((set) => ({
  status: null,
  loaded: false, // using this instead of (status === null) because it fixes the re-rendering issue
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
  setZonesMute: (mute, zones, source_id) => {
    set(produce((s) => {
      for (const i of getSourceZones(source_id, zones)) {
        for (const j of s.status.zones) {
          if (j.id === i.id) {
            j.mute = mute
          }
        }
      }
    }))
  },
  setZoneMute: (zid, mute) => {
    set(produce((s) => {
      for (const i of s.status.zones) {
          if (i.id === zid) {
            i.mute = mute
          }
        }
    }))
  },
  setGroupMute: (gid, mute) => {
    set(produce((s) => {
      let g = s.status.groups.filter((g) => g.id === gid)[0]
      for (const i of g.zones) {
        s.status.zones[i].mute = mute
      }
      g.mute = mute
    }))
  },
  fetch: async () => {
    // TODO make this not crash the app if the server is down
    const res = await fetch(`/api`)
    set({ status: await res.json(), loaded: true })
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
  },
  clearSourceZones: (sourceId) => {
    set(produce((s) => {
      let z = getSourceZones(sourceId, s.status.zones)
      fetch(`/api/zones`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          zones: z.map((z)=>z.id),
          update: {source_id: -1}
        })
      })
      for (const i in s.status.zones) {
        if(s.status.zones[i].source_id == sourceId){
          s.status.zones[i].source_id = -1
        }
      }
    }))
  }

}))

export const getIcon = (type) => {
  switch (type.toUpperCase()) {
    case "SPOTIFY":
      return spotify

    case "DLNA":
      return dlna

    case "BLUETOOTH":
      return bluetooth

    case "FM RADIO":
      return fmradio

    case "SHAIRPORT":
      return shairport

    case "PANDORA":
      return pandora

    case "PLEXAMP":
      return plexamp

    case "LMS":
      return lms

    case "RCA":
      return rca

    case "INTERNET RADIO":
      return internetradio

    default:
      return internetradio
  }
}

function App({ selectedPage }) {
  const [selectedSource, setSelectedSource] = useState(0);
  const isLoaded = useStatusStore((s) => s.loaded)
  const update = useStatusStore((s) => s.fetch)

  const setSelectedPage = (n) => {
    switch (n) {
      default:
        router.navigate('/home')
        break;
      case 1:
        router.navigate('/player')
        break;
      case 2:
        router.navigate('/browser')
        break;
      case 3:
        router.navigate('/settings')
        break;
    }
  }

  if (isLoaded == false) {

    return (
      useEffect(() => {
        const interval = setInterval(() => {
          update();
        }, UPDATE_INTERVAL);
        return () => clearInterval(interval);
      }, []),
      (<h1>Loading...</h1>)
    );
  }

  const Page = () => {
      switch(selectedPage) {
      default:
        return <Home selectedSource={selectedSource} setSelectedSource={(i)=>{setSelectedSource(i); setSelectedPage(1)}} />
      case 1:
        return <Player selectedSource={selectedSource} />
      case 2:
        return <div></div>
      case 3:
        return <Settings/>
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
        <MenuBar pageNumber={selectedPage} onChange={(n)=>{setSelectedPage(n)}}/>
      </div>
    )
  );
}

export default App;
