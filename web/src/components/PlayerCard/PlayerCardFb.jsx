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
import StreamerOutputBadge from "../StreamerOutputBadge/StreamerOutputBadge";
import Grid from "@mui/material/Grid/Grid";

import PropTypes from "prop-types";

const PlayerCardFb = ({ sourceId, setVol }) => {
    const [streamModalOpen, setStreamModalOpen] = useState(false);
    const [zoneModalOpen, setZoneModalOpen] = useState(false);
    const setSelectedSource = usePersistentStore((s) => s.setSelectedSource);
    const selected = usePersistentStore((s) => s.selectedSource) === sourceId;
    const img_url = useStatusStore((s) => s.status.sources[sourceId].info.img_url);
    const is_streamer = useStatusStore((s) => s.status.info.is_streamer);

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
                <Grid container className="top" spacing={0}>
                    <Grid className="content" item xs={11} sm={11} md={11} lg={11} xl={11}>
                        <StreamBadge sourceId={sourceId} onClick={openStreams} />
                    </Grid>
                    <Grid item xs={1} sm={1} md={1} lg={1} xl={1}>
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
                    </Grid>
                </Grid>
                <div className="content">
                    { !is_streamer && (
                        <div className="zones" >
                          <ZonesBadge sourceId={sourceId} onClick={openZones} />
                        </div>
                    )}
                    { is_streamer && (
                        <div className="zones" >
                            <StreamerOutputBadge sourceId={sourceId} />
                        </div>
                    )}
                    <SongInfo sourceId={sourceId} style={{maxWidth: "50%", textAlign: "right"}}/>
                </div>

                { !is_streamer && (
                    <CardVolumeSlider
                        sourceId={sourceId}
                        onChange={(event, vol) => {
                            setVol(sourceId, event, vol);
                        }}
                    />
                )}
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
    setVol: PropTypes.func,
    sourceId: PropTypes.any.isRequired,
};

export default PlayerCardFb;
