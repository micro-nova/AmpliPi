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
import { Grid, IconButton } from "@mui/material";
import StopProp from "@/components/StopProp/StopProp";
import StreamerOutputBadge from "../StreamerOutputBadge/StreamerOutputBadge";
import { getSourceZones } from "@/pages/Home/Home.jsx";

import PropTypes from "prop-types";

const PlayerCardFb = ({ sourceId, setVol }) => {
    const zones = getSourceZones(
        sourceId,
        useStatusStore((s) => s.status.zones)
    );
    const [streamModalOpen, setStreamModalOpen] = useState(false);
    const [zoneModalOpen, setZoneModalOpen] = useState(false);
    const setSelectedSource = usePersistentStore((s) => s.setSelectedSource);
    const selected = usePersistentStore((s) => s.selectedSource) === sourceId;
    const img_url = useStatusStore((s) => s.status.sources[sourceId].info.img_url);
    const is_streamer = useStatusStore((s) => s.status.info.is_streamer);
    const setSystemState = useStatusStore((s) => s.setSystemState);

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
        <Card backgroundImage={img_url} selected={selected} onClick={select} selectable>
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
                                }).then(res => {
                                    if(res.ok){res.json().then(s => setSystemState(s))}
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
                    <Grid
                        container
                        direction="row"
                        justifyContent="center"
                        alignItems="center"
                    >
                        <Grid item xs={6} sm={5} md={4}>
                            { !is_streamer && (
                                <div className="zones">
                                  <ZonesBadge sourceId={sourceId} onClick={openZones} />
                                </div>
                            )}
                            { is_streamer && (
                                <div className="streamer-outputs">
                                    <StreamerOutputBadge sourceId={sourceId} />
                                </div>
                            )}
                        </Grid>
                        <Grid item xs={0} sm={2} md={4}> {/* Spacer */} </Grid>
                        <Grid item xs={6} sm={5} md={4}>
                            <SongInfo sourceId={sourceId}/>
                        </Grid>

                    </Grid>
                </div>

                { !is_streamer && zones.length > 0 && (
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
