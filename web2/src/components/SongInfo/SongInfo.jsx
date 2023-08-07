import React from "react";
import "./SongInfo.scss";
import { useStatusStore } from "@/App.jsx";

import PropTypes from "prop-types";

const SongInfo = ({
    sourceId,
    artistClassName,
    albumClassName,
    trackClassName
}) => {

    const info = useStatusStore(state => state.status.sources[sourceId].info);

    artistClassName = "artist-name " + artistClassName;
    albumClassName = "album-name " + albumClassName;
    trackClassName = "track-name " + trackClassName;

    return (
        <div className="song-info">
            <div className={artistClassName}>{info.artist}</div>
            <div className={albumClassName}>{info.album}</div>
            <div className={trackClassName}>{info.track}</div>
        </div>
    );
};
SongInfo.propTypes = {
    sourceId: PropTypes.any.isRequired,
    artistClassName: PropTypes.string.isRequired,
    albumClassName: PropTypes.string.isRequired,
    trackClassName : PropTypes.string.isRequired
};

export default SongInfo;
