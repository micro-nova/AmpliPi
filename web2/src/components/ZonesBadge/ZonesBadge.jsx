import React from "react";
import "./ZonesBadge.scss";
import { getSourceZones } from "@/pages/Home/Home.jsx";
import { useStatusStore } from "@/App.jsx";

import PropTypes from "prop-types";

const ZonesBadge = ({ sourceId }) => {
    const allZones = useStatusStore((s) => s.status.zones);
    const usedZones = getSourceZones(sourceId, allZones);

    let zones_text = "";
    if(usedZones.length > 2) {
        zones_text = `${usedZones[0].name} and ${usedZones.length - 1} more`;
    } else if(usedZones.length == 2) {
        zones_text = `${usedZones[0].name} and ${usedZones[1].name}`;
    } else if(usedZones.length == 1) {
        zones_text = `${usedZones[0].name}`;
    }

    return (
        <div className='zone-text'>
            {zones_text}
        </div>
    );
};
ZonesBadge.propTypes = {
    sourceId: PropTypes.any.isRequired,
};

export default ZonesBadge;
