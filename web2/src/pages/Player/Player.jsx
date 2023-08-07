import React from "react";
import StreamBar from "@/components/StreamBar/StreamBar";
import SongInfo from "@/components/SongInfo/SongInfo";
import MediaControl from "@/components/MediaControl/MediaControl";
import "./Player.scss";
import { useStatusStore } from "@/App.jsx";

import PropTypes from "prop-types";

const Player = ({ selectedSource }) => {
    const img_url = useStatusStore((s) => s.status.sources[selectedSource].info.img_url);

    return (
        <>
            <StreamBar sourceId={selectedSource}></StreamBar>
            <div className="player-outer">
                <div className="player-inner">
                    <img src={img_url} className="player-album-art" />
                    <SongInfo sourceId={selectedSource} artistClassName="player-info-title" albumClassName="player-info-album" trackClassName="player-info-track" />
                    <MediaControl selectedSource={selectedSource}/>
                </div>
            </div>
        </>
    );
};
Player.propTypes = {
    selectedSource: PropTypes.any.isRequired,
};

export default Player;
