import React from "react";
import { create } from "zustand";
import { init as initApm } from "@elastic/apm-rum";
// import { useCookies } from "react-cookie";
import "@/App.scss";
import Home from "@/pages/Home/Home";
import Player from "@/pages/Player/Player";
import MenuBar from "./components/MenuBar/MenuBar";
import produce from "immer";
import { applyPlayerVol } from "./components/CardVolumeSlider/CardVolumeSlider";
import { persist, createJSONStorage } from "zustand/middleware";
import Settings from "@/pages/Settings/Settings";
import { getSourceZones } from "@/pages/Home/Home";
import DisconnectedIcon from "./components/DisconnectedIcon/DisconnectedIcon";

import PropTypes from "prop-types";

// const UPDATE_INTERVAL = 1000; Commented out while unused

var apm = initApm({
  serviceName: "Amplipi",
  serverUrl: "http://localhost:8200",
  serviceVersion: "",
  environment: "Amplipi"
});

// holds onto the selectedSource state so that it persists between refreshes
export const usePersistentStore = create(
    persist(
        (set) => ({
            selectedSource: 0,
            setSelectedSource: (selected) => {
                set({ selectedSource: selected });
            },
        }),
        {
            name: "persistent-store",
            storage: createJSONStorage(() => localStorage),
        }
    )
);

// holds onto non-persistent state
export const useStatusStore = create((set, get) => ({
    status: null,
    skipUpdate: false,
    loaded: false, // using this instead of (status === null) because it fixes the re-rendering issue
    disconnected: true,
    setZonesVol: (vol, zones, sourceId) => {
        set(
            produce((s) => {
                s.skipUpdate = true;
                applyPlayerVol(vol, zones, sourceId, (zone_id, new_vol) => {
                    for (const i in s.status.zones) {
                        if (s.status.zones[i].id === zone_id) {
                            s.status.zones[i].vol_f = new_vol;
                        }
                    }
                });
                updateGroupVols(s);
            })
        );
    },
    setZonesMute: (mute, zones, source_id) => {
        set(
            produce((s) => {
                for (const i of getSourceZones(source_id, zones)) {
                    for (const j of s.status.zones) {
                        if (j.id === i.id) {
                            j.mute = mute;
                        }
                    }
                }
            })
        );
    },
    setZoneMute: (zid, mute) => {
        set(
            produce((s) => {
                for (const i of s.status.zones) {
                    if (i.id === zid) {
                        i.mute = mute;
                    }
                }
            })
        );
    },
    setGroupMute: (gid, mute) => {
        set(
            produce((s) => {
                let g = s.status.groups.filter((g) => g.id === gid)[0];
                for (const i of g.zones) {
                    s.status.zones[i].mute = mute;
                }
                g.mute = mute;
            })
        );
    },
    setSourceState: (sourceId, state) => {
        set(
            produce((s) => {
                s.skipUpdate = true;
                s.status.sources[sourceId].info.state = state;
            })
        );
    },
    fetch: () => {
    // if (get().skipUpdate) {
    //   set({ skipUpdate: false })
    //   return
    // }
        fetch("/api")
            .then((res) => {
                if (res.ok) {
                    res.json().then((s) => {
                        if (get().skipUpdate) {
                            set({ skipUpdate: false });
                        } else {
                            set({ status: s, loaded: true, disconnected: false });
                        }
                    });
                } else {
                    set({ disconnected: true });
                }
            })
            .catch(() => {
                set({ disconnected: true });
            });
    },
    setZoneVol: (zoneId, new_vol) => {
        set(
            produce((s) => {
                s.skipUpdate = true;
                s.status.zones[zoneId].vol_f = new_vol;

                updateGroupVols(s);
            })
        );
    },
    setGroupVol: (groupId, new_vol) => {
        set(
            produce((s) => {
                const g = s.status.groups.filter((g) => g.id === groupId)[0];
                for (const i of g.zones) {
                    s.skipUpdate = true;
                    s.status.zones[i].vol_f = new_vol;
                }

                updateGroupVols(s);
            })
        );
    },
    clearSourceZones: (sourceId) => {
        set(
            produce((s) => {
                let z = getSourceZones(sourceId, s.status.zones);
                fetch("/api/zones", {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        zones: z.map((z) => z.id),
                        update: { source_id: -1 },
                    }),
                });
                for (const i in s.status.zones) {
                    if (s.status.zones[i].source_id == sourceId) {
                        s.status.zones[i].source_id = -1;
                    }
                }
            })
        );
    },
}));

const updateGroupVols = (s) => {
    s.status.groups.forEach((g) => {
        if (g.zones.length > 1) {
            const vols = g.zones.map((id) => s.status.zones[id].vol_f);
            let calculated_vol = Math.min(...vols) * 0.5 + Math.max(...vols) * 0.5;
            g.vol_f = calculated_vol;
        } else if (g.zones.length == 1) {
            // ID is not defined, needs fixed
            g.vol_f = s.status.zones[id].vol_f;
        }
    });
};

const Page = ({ selectedPage }) => {
    switch (selectedPage) {
    default:
        return <Home />;
    case 1:
        return <Player />;
    case 2:
        return <div></div>;
    case 3:
        return <Settings />;
    }
};
Page.propTypes = {
    selectedPage: PropTypes.any.isRequired,
};

const App = ({ selectedPage }) => {
    return (
        <div className="app">
            <DisconnectedIcon />
            <div style={{ paddingBottom: "56px" }}>
                <Page selectedPage={selectedPage} />
            </div>
            <MenuBar pageNumber={selectedPage} />
        </div>
    );
};
App.propTypes = {
    selectedPage: PropTypes.any.isRequired,
};

export default App;
