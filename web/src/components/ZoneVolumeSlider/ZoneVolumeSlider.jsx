import React from "react";
import "./ZoneVolumeSlider.scss";
import { useStatusStore } from "@/App";
import VolumeSlider from "../VolumeSlider/VolumeSlider";

import PropTypes from "prop-types";

let sendingRequestCount = 0;

// Volume slider for individual zone in volume drawer
const ZoneVolumeSlider = ({ zoneId }) => {
    const zoneName = useStatusStore((s) => s.status.zones[zoneId].name);
    const volume = useStatusStore((s) => s.status.zones[zoneId].vol_f);
    const mute = useStatusStore((s) => s.status.zones[zoneId].mute);
    const lock = useStatusStore((s) => s.status.zones[zoneId].lock);
    const setZoneVol = useStatusStore((s) => s.setZoneVol);
    const setZoneMute = useStatusStore((s) => s.setZoneMute);
    const setZoneLock = useStatusStore((s) => s.setZoneLock);

    const setVol = (vol, force = false) => {
      if(!lock){
        setZoneVol(zoneId, vol);

        if (sendingRequestCount <= 0 || force) {
            sendingRequestCount += 1;

            fetch(`/api/zones/${zoneId}`, {
                method: "PATCH",
                headers: {
                    "Content-type": "application/json",
                },
                body: JSON.stringify({ vol_f: vol, mute: false }),
            }).then(() => {
                sendingRequestCount -= 1;
            });
        }
      }
    };

    const setMute = (mute) => {
        setZoneMute(zoneId, mute);

        fetch(`/api/zones/${zoneId}`, {
            method: "PATCH",
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({ mute: mute }),
        });
    };

    const setLock = (lock) => {
        setZoneLock(zoneId, lock);

        fetch(`/api/zones/${zoneId}`, {
            method: "PATCH",
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({ lock: lock }),
        });
    };

    return (
        <div className="zone-volume-container">
            {zoneName}
            <VolumeSlider
                lock={lock}
                setLock={setLock}
                mute={mute}
                setMute={setMute}
                vol={volume}
                setVol={setVol}
            />
        </div>
    );
};
ZoneVolumeSlider.propTypes = {
    zoneId: PropTypes.number.isRequired,
};

export default ZoneVolumeSlider;
