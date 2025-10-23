import React from "react";
import "./ZoneVolumeSlider.scss";
import { useStatusStore } from "@/App";
import VolumeSlider from "../VolumeSlider/VolumeSlider";

import PropTypes from "prop-types";

let sendingRequestCount = 0;

// Volume slider for individual zone in volume drawer
const ZoneVolumeSlider = ({ zoneId, alone }) => {
    const setSystemState = useStatusStore((s) => s.setSystemState);
    const zoneName = useStatusStore((s) => s.status.zones[zoneId].name);
    const volume = useStatusStore((s) => s.status.zones[zoneId].vol_f);
    const mute = useStatusStore((s) => s.status.zones[zoneId].mute);
    const setZoneVol = useStatusStore((s) => s.setZoneVol);
    const setZoneMute = useStatusStore((s) => s.setZoneMute);

    const setVol = (vol, force = false) => {
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
    };

    const setMute = (mute) => {
        setZoneMute(zoneId, mute);

        fetch(`/api/zones/${zoneId}`, {
            method: "PATCH",
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({ mute: mute }),
        }).then(res => {
            if(res.ok){res.json().then(s => setSystemState(s));}
        });
    };

    return (
        <div className={`zone-volume-container ${alone ? "alone" : "grouped"}`}>
            {zoneName}
            <VolumeSlider
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
    alone: PropTypes.bool,
};
ZoneVolumeSlider.defaultProps = {
    alone: false,
}

export default ZoneVolumeSlider;
