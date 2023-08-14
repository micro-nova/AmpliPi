import React from "react";
import Card from "@/components/Card/Card";
import StreamBadge from "@/components/StreamBadge/StreamBadge";
import SongInfo from "../SongInfo/SongInfo";
import CardVolumeSlider from "../CardVolumeSlider/CardVolumeSlider";
import { useState } from "react";
import ZonesBadge from "../ZonesBadge/ZonesBadge";
import StreamsModal from "../StreamsModal/StreamsModal";
import ZonesModal from "../ZonesModal/ZonesModal";
import { usePersistentStore, useStatusStore } from "@/App.jsx";
import { router } from "@/main";
import "./PlayerCardFb.scss";
import CloseIcon from "@mui/icons-material/Close";
import { IconButton } from "@mui/material";
import StopProp from "@/components/StopProp/StopProp";

import PropTypes from "prop-types";

const PlayerCardFb = ({ sourceId, setVol }) => {
    const [streamModalOpen, setStreamModalOpen] = useState(false);
    const [zoneModalOpen, setZoneModalOpen] = useState(false);
    const setSelectedSource = usePersistentStore((s) => s.setSelectedSource);
    const selected = usePersistentStore((s) => s.selectedSource) === sourceId;
    const img_url = useStatusStore((s) => s.status.sources[sourceId].info.img_url);

    const select = () => {
        if (selected) {
            router.navigate("/player");
        }

        setSelectedSource(sourceId);
    };

    const openStreams = () => {
        setStreamModalOpen(true);
    };

    const openZones = () => {
        setZoneModalOpen(true);
    };

    return (
        <Card backgroundImage={img_url} selected={selected} onClick={select}>
            <div className="container">
                <div className="top">
                    <StreamBadge sourceId={sourceId} onClick={openStreams} />
                    <StopProp>
                        <IconButton
                            onClick={() => {
                                fetch(`/api/sources/${sourceId}`, {
                                    method: "PATCH",
                                    headers: {
                                        "Content-type": "application/json",
                                    },
                                    body: JSON.stringify({ input: "None" }),
                                });
                            }}
                        >
                            <CloseIcon
                                style={{ width: "2rem", height: "2rem" }}
                            />
                        </IconButton>
                    </StopProp>
                </div>
                <div className="content">
                    <div className="zones">
                        <ZonesBadge sourceId={sourceId} onClick={openZones} />
                    </div>
                    <SongInfo sourceId={sourceId} />
                </div>

                <CardVolumeSlider
                    sourceId={sourceId}
                    onChange={(event, vol) => {
                        setVol(sourceId, event, vol);
                    }}
                />
            </div>

            {streamModalOpen && (
                <StreamsModal
                    sourceId={sourceId}
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
        </Card>
    );
};
PlayerCardFb.propTypes = {
    setVol: PropTypes.func.isRequired,
    sourceId: PropTypes.any.isRequired,
};

export default PlayerCardFb;
