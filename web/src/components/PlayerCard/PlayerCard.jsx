import React from "react";
import { usePersistentStore } from "@/App.jsx";
import Card from "@/components/Card/Card";
import "./PlayerCard.scss";
import StreamBadge from "@/components/StreamBadge/StreamBadge";
import SongInfo from "../SongInfo/SongInfo";
import CardVolumeSlider from "../CardVolumeSlider/CardVolumeSlider";
import PlayerImage from "../PlayerImage/PlayerImage";
import ZonesBadge from "../ZonesBadge/ZonesBadge";
import StreamsModal from "../StreamsModal/StreamsModal";
import ZonesModal from "../ZonesModal/ZonesModal";
import { router } from "@/main";

import PropTypes from "prop-types";

const PlayerCard = ({ sourceId, setVol }) => {
    const [streamModalOpen, setStreamModalOpen] = React.useState(false);
    const [zoneModalOpen, setZoneModalOpen] = React.useState(false);
    const setSelectedSource = usePersistentStore((s) => s.setSelectedSource);
    const selected = usePersistentStore((s) => s.selectedSource) === sourceId;
    const is_streamer = useStatusStore((s) => s.status.info.is_streamer);

    const select = () => {
        if (selected) {
            router.navigate("/player");
        }

        setSelectedSource(sourceId);
    };

    return (
        <Card selected={selected}>
            <div className="outer">
                <div
                    className="content stream-name-container"
                    onClick={() => {
                        setStreamModalOpen(true);
                    }}
                >
                    <StreamBadge sourceId={sourceId} />
                </div>
                {!is_streamer && (
                    <div
                        className="content"
                        onClick={() => {
                            setZoneModalOpen(true);
                        }}
                    >
                        <ZonesBadge sourceId={sourceId} />
                    </div>
                )}
                <div className="content album-art" onClick={select}>
                    <div className="image-container">
                        <PlayerImage sourceId={sourceId} />
                    </div>
                </div>
                <div className="content song-info" onClick={select}>
                    <SongInfo sourceId={sourceId} />
                </div>
                {!is_streamer && (
                    <div className="content vol">
                        <CardVolumeSlider
                            sourceId={sourceId}
                            onChange={(event, vol) => {
                                setVol(sourceId, event, vol);
                            }}
                        />
                    </div>
                )}
                {streamModalOpen && (
                    <StreamsModal
                        sourceId={sourceId}
                        setStreamModalOpen={setStreamModalOpen}
                        onClose={() => setStreamModalOpen(false)}
                    />
                )}
                {zoneModalOpen && (
                    <ZonesModal
                        sourceId={sourceId}
                        setZoneModalOpen={setZoneModalOpen}
                        onClose={() => setZoneModalOpen(false)}
                    />
                )}
            </div>
        </Card>
    );
};
PlayerCard.propTypes = {
    setVol: PropTypes.func.isRequired,
    sourceId: PropTypes.any.isRequired,
};

export default PlayerCard;
