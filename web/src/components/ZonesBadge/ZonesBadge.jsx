import React from "react";
import "./ZonesBadge.scss";
import { getSourceZones } from "@/pages/Home/Home.jsx";
import { useStatusStore } from "@/App.jsx";
import Chip from "../Chip/Chip";
import { getFittestRep } from "@/utils/GroupZoneFiltering";
import Grid from "@mui/material/Grid/Grid";

import PropTypes from "prop-types";

const ZoneGroupChip = ({ zoneGroup, onClick }) => {
    return (
        <Grid item xs={"auto"} sm={"auto"} md={"auto"} lg={"auto"} xl={"auto"}>
            <Chip onClick={onClick} style={{maxWidth: "35vw"}}>
                <div className="zone-text">{zoneGroup.name}</div>
            </Chip>
        </Grid>
    );
};
ZoneGroupChip.propTypes = {
    zoneGroup: PropTypes.any.isRequired,
    onClick: PropTypes.func.isRequired,
};

const ZonesBadge = ({ sourceId, onClick }) => {
    const zones = getSourceZones(
        sourceId,
        useStatusStore((s) => s.status.zones)
    );
    const groups = getSourceZones(
        sourceId,
        useStatusStore((s) => s.status.groups)
    );

    // compute the best representation of the zones and groups
    const { zones: bestZones, groups: bestGroups } = getFittestRep(zones, groups);

    const combined = [...bestGroups, ...bestZones];

    let chips = [];

    // TODO: cleanup. or maybe even just get rid of this resize logic.
    // only does anything on desktop, and we are going to have a
    // custom desktop version anyway so this will be unnecessary
    // in the future.
    function getWindowDimensions() {
        const { innerWidth: width, innerHeight: height } = window;
        return {
            width,
            height,
        };
    }

    const [windowDimensions, setWindowDimensions] = React.useState(
        getWindowDimensions()
    );

    React.useEffect(() => {
        function handleResize() {
            setWindowDimensions(getWindowDimensions());
        }

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    const { width } = windowDimensions;
    const amount = 2 + Math.max(2 * Math.floor((width - 550) / 220), 0);

    if (combined.length >= amount) {
        for (let i = 0; i < amount - 1; i++) {
            const item = combined[i];
            chips.push(<ZoneGroupChip key={i} onClick={onClick} zoneGroup={item} />);
        }
        chips.push(
            <ZoneGroupChip
                key={1}
                onClick={onClick}
                zoneGroup={{ name: `+${combined.length - (amount - 1)} more` }}
            />
        );
    } else if (combined.length > 0) {
        for (const [i, item] of combined.entries()) {
            chips.push(<ZoneGroupChip key={i} onClick={onClick} zoneGroup={item} />);
        }
    } else {
        chips.push(
            <ZoneGroupChip
                key={0}
                onClick={onClick}
                zoneGroup={{ name: "Add Zones" }}
            />
        );
    }

    return (
        <div className="zones-container">
            <Grid container padding={2}>
                {chips}
            </Grid>
        </div>
    );
};
ZonesBadge.propTypes = {
    sourceId: PropTypes.any.isRequired,
    onClick: PropTypes.func.isRequired,
};

export default ZonesBadge;
