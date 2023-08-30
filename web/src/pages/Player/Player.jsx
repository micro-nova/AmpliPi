import React from "react";
import StreamBar from "@/components/StreamBar/StreamBar";
import SongInfo from "@/components/SongInfo/SongInfo";
import MediaControl from "@/components/MediaControl/MediaControl";
import "./Player.scss";
import { useStatusStore, usePersistentStore } from "@/App.jsx";
import CardVolumeSlider from "@/components/CardVolumeSlider/CardVolumeSlider";
import { IconButton } from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { useState } from "react";
import VolumeZones from "@/components/VolumeZones/VolumeZones";
import Card from "@/components/Card/Card";
import { getSourceInputType } from "@/utils/getSourceInputType";

const Player = () => {
    const selectedSourceId = usePersistentStore((s) => s.selectedSource);
    // TODO: dont index into sources. id isn't guarenteed to line up with order
    const img_url = useStatusStore(
        (s) => s.status.sources[selectedSourceId].info.img_url
    );
    const selectedSource = useStatusStore(
        (s) => s.status.sources[selectedSourceId]
    );
    const sourceIsInactive = getSourceInputType(selectedSource) === "none";
    const [expanded, setExpanded] = useState(false);
    const [alone, setAlone] = useState(false);

    if (sourceIsInactive) {
        return (
            <div className="player-outer">
                <div className="player-stopped-message">No Player Selected!</div>
            </div>
        );
    }

    return (
        <div className="player-outer">
            <StreamBar sourceId={selectedSourceId} />
            <div className="player-inner">
                <img src={img_url} className="player-album-art" />
                <SongInfo
                    sourceId={selectedSourceId}
                    artistClassName="player-info-title"
                    albumClassName="player-info-album"
                    trackClassName="player-info-track"
                />
                <MediaControl selectedSource={selectedSourceId} />
            </div>

            {!alone && <Card className="player-volume-slider">
                <CardVolumeSlider sourceId={selectedSourceId} />
                <IconButton onClick={() => setExpanded(!expanded)}>
                    {expanded ? (
                        <KeyboardArrowUpIcon
                            className="player-volume-expand-button"
                            style={{ width: "3rem", height: "3rem" }}
                        />
                    ) : (
                        <KeyboardArrowDownIcon
                            className="player-volume-expand-button"
                            style={{ width: "3rem", height: "3rem" }}
                        />
                    )}
                </IconButton>
            </Card>}
            <VolumeZones open={(expanded || alone)} setAlone={setAlone} sourceId={selectedSourceId} />
        </div>
    );
};

export default Player;
