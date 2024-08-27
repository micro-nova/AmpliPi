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
import { getSourceInputType } from "@/utils/getSourceInputType";
import Chip from "@/components/Chip/Chip";
import Grid from "@mui/material/Grid/Grid"
import selectActiveSource from "@/utils/selectActiveSource";

import { getSourceZones } from "@/pages/Home/Home";

import { getFittestRep } from "@/utils/GroupZoneFiltering";

const Player = () => {
    const [streamsModalOpen, setStreamsModalOpen] = React.useState(false);
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

    return (
        <div className="player-outer">
            {streamsModalOpen && (
                <StreamsModal
                    sourceId={selectedSourceId}
                    onClose={() => setStreamsModalOpen(false)}
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
                    <img src={img_url} className="player-album-art" />
                    <SongInfo sourceId={selectedSourceId} />
                </Grid>
                <Grid item xs={2} sm={4} md={4}>
                    <MediaControl selectedSource={selectedSourceId} />
                </Grid>
            </Grid>
            {/* There are many sub-divs classed player-inner here because formatting was strange otherwise */}
            <div className="player-inner">
            </div>
            <div className="player-inner">
            </div>
            <div className="player-inner">
            </div>

            {!alone && !is_streamer && zones.length > 0 && (
                <Card className="player-volume-slider">
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
                </Card>
            )}
            <VolumeZones open={(expanded || alone)} sourceId={selectedSourceId} zones={zonesLeft} groups={usedGroups} groupsLeft={groupsLeft} />
        </div>
    );
};

export default Player;
