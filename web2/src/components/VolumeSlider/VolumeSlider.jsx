import React from "react";
import Slider from "@mui/material/Slider";
import { getSourceZones } from "@/pages/Home/Home";
import { useStatusStore } from "@/App";
import "./VolumeSlider.scss";

import PropTypes from "prop-types";

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


let sendingPacketCount = 0;

const VolumeSlider = ({sourceId}) => {
    const zones = useStatusStore((s) => s.status.zones);
    const setZonesVol = useStatusStore((s) => s.setZonesVol);

    const setPlayerVolRaw = (vol) => applyPlayerVol(vol, zones, sourceId, (zone_id, new_vol) => {
        console.log(`going to send packet: ${sendingPacketCount}`);
        sendingPacketCount += 1;
        console.log(`sending packet: ${sendingPacketCount}`);
        fetch(`/api/zones/${zone_id}`, {
            method: "PATCH",
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({ vol_f: new_vol }),
        }).then(() => {sendingPacketCount -= 1; console.log(`packet sent: ${sendingPacketCount}`);});
    });

    const setPlayerVol = (vol) => {
        if (sendingPacketCount <= 0) {
            setPlayerVolRaw(vol);
            console.log("updating vol");
        } else {
            console.log("skipping vol update, " + sendingPacketCount + " already sending");
        }
    };

    const value = getPlayerVol(sourceId, zones);

    const setValue = (vol) => {
        setZonesVol(vol, zones, sourceId);
    };

    return (
    // React.useEffect(() => {
    //   setValue(vol);
    // }, [vol]),
        <Slider
            className="volume-slider"
            min={0}
            step={0.01}
            max={1}
            value={value}
            onChange={(event, val)=>{setPlayerVol(val); setValue(val);}}
        />
    );
};
VolumeSlider.propTypes = {
    sourceId: PropTypes.any.isRequired,
};

export default VolumeSlider;
