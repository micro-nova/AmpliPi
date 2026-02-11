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
import StreamsModal from "@/components/StreamsModal/StreamsModal";
import ZonesModal from "@/components/ZonesModal/ZonesModal";
import { getSourceInputType } from "@/utils/getSourceInputType";
import Chip from "@/components/Chip/Chip";
import Grid from "@mui/material/Grid/Grid"
import selectActiveSource from "@/utils/selectActiveSource";
import Box from "@mui/material/Box/Box";

import { getSourceZones } from "@/pages/Home/Home";

import { getFittestRep } from "@/utils/GroupZoneFiltering";

const Player = () => {
    const [streamsModalOpen, setStreamsModalOpen] = React.useState(false);
    const [zonesModalOpen, setZonesModalOpen] = React.useState(false);
    const selectedSourceId = usePersistentStore((s) => s.selectedSource);
    // TODO: Don't index into sources. id isn't guaranteed to line up with order
    const img_url = useStatusStore(
        (s) => s.status.sources[selectedSourceId].info.img_url
    );
    const selectedSource = useStatusStore(
        (s) => s.status.sources[selectedSourceId]
    );
    const sourceIsInactive = getSourceInputType(selectedSource) === "none";
    const [expanded, setExpanded] = useState(false);
    const is_streamer = useStatusStore((s) => s.status.info.is_streamer);

    if (sourceIsInactive) {
        return (
            <div className="player-outer">
                <div className="player-stopped-message">No Player Selected!</div>
            </div>
        );
    }

    const zones = getSourceZones(
        selectedSourceId,
        useStatusStore((s) => s.status.zones)
    );
    const groups = getSourceZones(
        selectedSourceId,
        useStatusStore((s) => s.status.groups)
    );

    // compute the best representation of the zones and groups
    const { zones: zonesLeft, groups: usedGroups } = getFittestRep(zones, groups);

    const groupsLeft = groups.filter(
        (g) => !usedGroups.map((ug) => ug.id).includes(g.id)
    );
    // This is a bootleg XOR statement, only works if there is exactly one zone or exactly one group, no more than that and not both
    const alone = ((usedGroups.length == 1) || (zonesLeft.length == 1)) && !((usedGroups.length > 0) && (zonesLeft.length > 0));

    selectActiveSource();

    function DropdownArrow() {
        // If on mobile, inital dropdown is at the bottom of the screen and expands upwards so the arrow should point up
        // If on desktop, initial dropdown is in the middle of the screen and expands downwards so the arrow should point down
        const isMobile = window.matchMedia("(max-width: 435px)").matches;
        const Icon = isMobile ? (expanded ? KeyboardArrowDownIcon : KeyboardArrowUpIcon) : (expanded ? KeyboardArrowUpIcon : KeyboardArrowDownIcon);
        return(
            <Icon
                className="player-volume-expand-button"
                style={{ width: "3rem", height: "3rem" }}
            />
        )
    }

    return (
        <div className="player-outer">
            {streamsModalOpen && (
                <StreamsModal
                    sourceId={selectedSourceId}
                    onClose={() => setStreamsModalOpen(false)}
                />
            )}

            {zonesModalOpen && (
                <ZonesModal
                    sourceId={selectedSourceId}
                    setZoneModalOpen={setZonesModalOpen}
                    onClose={() => setZonesModalOpen(false)}
                />
            )}
            <Grid
              container
              direction="column"
              justifyContent="center"
              alignItems="center"
            >
                <Grid item xs={2} sm={4} md={4}>
                    <div className="stream-title" >
                        <Chip style={{width: "100%"}}>
                            <StreamBar sourceId={selectedSourceId} onClick={() => {setStreamsModalOpen(true);}}/>
                        </Chip>
                    </div>
                </Grid>
                <Grid item xs={2} sm={4} md={4} style={{maxWidth: "22rem"}}>
                    <Box
                        className="album-art-container"
                        sx={{
                          display: 'flex',
                          justifyContent: 'center',
                          alignItems: 'center',
                        }}
                    >
                        <img src={img_url} className="player-album-art" />
                    </Box>
                    <SongInfo sourceId={selectedSourceId} />
                </Grid>
            </Grid>

            <div className={alone ? "solo-media-controls" : "grouped-media-controls" } >
                <MediaControl selectedSource={selectedSourceId} />
            </div>
            { !is_streamer && (
                <Card className="player-volume-container">
                    { (zones.length > 0) && (
                        <div className="player-volume-header">
                            <CardVolumeSlider sourceId={selectedSourceId} />
                            <IconButton onClick={() => setExpanded(!expanded)}>
                                <DropdownArrow />
                            </IconButton>
                        </div>
                    )}
                    <div className={`player-volume-body ${(expanded) && "expanded-volume-body pill-scrollbar"}`}>
                        <VolumeZones setZonesModalOpen={setZonesModalOpen} open={(expanded)} sourceId={selectedSourceId} zones={zonesLeft} groups={usedGroups} groupsLeft={groupsLeft} />
                    </div>
                </Card>
            ) }
        </div>
    );
};

export default Player;
