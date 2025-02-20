import React from "react";

import PropTypes from "prop-types";
import "./CardVolumeSlider.scss";
import { getSourceZones } from "@/pages/Home/Home";
import { useStatusStore } from "@/App";
import VolumeSlider from "@/components/VolumeSlider/VolumeSlider";

const getPlayerVol = (sourceId, zones) => {
    let vol = 0;
    let n = 0;
    for (const i of getSourceZones(sourceId, zones)) {
        n += 1;
        vol += i.vol_f;
    }

    const avg = vol / n;

    if (isNaN(avg)) {
        return 0;
    } else {
        return avg;
    }
};

export const applyPlayerVol = (vol, zones, sourceId, apply) => {
    let delta = vol - getPlayerVol(sourceId, zones);

    for (let i of getSourceZones(sourceId, zones)) {
        let set_pt = Math.max(0, Math.min(1, i.vol_f + delta));
        apply(i.id, set_pt);
    }
};

// cumulativeDelta reflects the amount of movement that the
let cumulativeDelta = 0;
let sendingPacketCount = 0;

// main volume slider on player and volume slider on player card
const CardVolumeSlider = ({ sourceId }) => {
    const zones = useStatusStore((s) => s.status.zones);
    const setZonesVol = useStatusStore((s) => s.setZonesVol);
    const setZonesMute = useStatusStore((s) => s.setZonesMute);

    // needed to ensure that polling doesn't cause the delta volume to be made inacurrate during volume slider interactions
    const skipNextUpdate = useStatusStore((s) => s.skipNextUpdate);

    const value = getPlayerVol(sourceId, zones);

    const setValue = (vol) => {
        setZonesVol(vol, zones, sourceId);
        setZonesMute(false, zones, sourceId);
    };

    function setPlayerVol(vol, val) {
        cumulativeDelta += vol - val;

        if(sendingPacketCount <= 0){
            sendingPacketCount += 1;

            const delta = cumulativeDelta;

            fetch("/api/zones", {
                method: "PATCH",
                headers: {
                    "Content-type": "application/json",
                },
                body: JSON.stringify({
                    zones: getSourceZones(sourceId, zones).map((z) => z.id),
                    update: { vol_delta_f: cumulativeDelta, mute: false },
                }),
            }).then(() => {
                // NOTE: This used to just set cumulativeDelta to 0
                // that would skip all accumulated delta from fetch start to backend response time
                // causing jittering issues
                cumulativeDelta -= delta;
                sendingPacketCount -= 1;
            });
        }
    };

    const mute = getSourceZones(sourceId, zones)
        .map((z) => z.mute)
        .reduce((a, b) => a && b, true);


    const setMute = (mute) => {
        setZonesMute(mute, zones, sourceId);
        fetch("/api/zones", {
            method: "PATCH",
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({
                zones: getSourceZones(sourceId, zones).map((z) => z.id),
                update: { mute: mute },
            }),
        });
    };

    return (
        <div className="volume-slider">
            <VolumeSlider
                vol={value}
                mute={mute}
                setMute={setMute}
                setVol={(val, force) => {
                    // Cannot use value directly as that changes during the request when setValue() is called
                    // Cannot call setValue() as a .then() after the request as that causes the ui to feel unresponsive and choppy
                    let current_val = value;
                    setPlayerVol(val, current_val);
                    setValue(val);
                    skipNextUpdate();
                }}
                disabled={getSourceZones(sourceId, zones) == 0}
            />
        </div>
    );
};
CardVolumeSlider.propTypes = {
    sourceId: PropTypes.any.isRequired,
};

export default CardVolumeSlider;
