import React from "react";
import "./StreamerOutputBadge.scss";
import { getSourceZones } from "@/pages/Home/Home.jsx";
import { useStatusStore } from "@/App.jsx";
import Chip from "../Chip/Chip";
import { getFittestRep } from "@/utils/GroupZoneFiltering";

import PropTypes from "prop-types";

const StreamerOutputChip = ({ streamerOutput, onClick }) => {
    return (
        <Chip onClick={onClick}>
            <div className="streamer-output-text">{streamerOutput.name}</div>
        </Chip>
    );
};
StreamerOutputChip.propTypes = {
    streamerOutput: PropTypes.any.isRequired,
    onClick: PropTypes.func,
};

const StreamerOutputBadge = ({ sourceId, onClick }) => {
    const output = useStatusStore((s) => 
        s.status.sources.find((i) => i.id == sourceId)
    );

    const chip = <StreamerOutputChip key={sourceId} onClick={onClick} streamerOutput={output} />
    return <div className="zones-container">{chip}</div>;
};
StreamerOutputBadge.propTypes = {
    sourceId: PropTypes.any.isRequired,
    onClick: PropTypes.func,
};

export default StreamerOutputBadge;
