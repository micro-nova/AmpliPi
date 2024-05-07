import React from "react";
import "./SongInfo.scss";
import { useStatusStore } from "@/App.jsx";

import PropTypes from "prop-types";

const SongInfo = ({
    sourceId,
}) => {
    const info = useStatusStore((state) => state.status.sources[sourceId].info);

    return (
        <div className="song-info">
            <div className={"artist-name player-info-title"}>{info.artist}</div>
            <div className={"album-name player-info-album"}>{info.album}</div>
            <div className={"track-name player-info-track"}>{info.track}</div>
        </div>
    );
};
SongInfo.propTypes = {
    sourceId: PropTypes.any.isRequired,
};

export default SongInfo;
