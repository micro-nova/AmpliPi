import React from "react";
import PlayerCardFb from "@/components/PlayerCard/PlayerCardFb";
import "./Home.scss";
import { useStatusStore } from "@/App.jsx";
import ZonesModal from "@/components/ZonesModal/ZonesModal";
import StreamsModal from "@/components/StreamsModal/StreamsModal";
import PresetsModal from "@/components/PresetsModal/PresetsModal";
import StreamerOutputModal from "@/components/StreamerOutputModal/StreamerOutputModal";
import { executeApplyAction } from "@/components/StreamsModal/StreamsModal";
import Grid from "@mui/material/Grid/Grid";

import PropTypes from "prop-types";

export const getSourceZones = (source_id, zones) => {
    let matches = [];
    for (const i of zones) {
        if (i.source_id == source_id) {
            matches.push(i);
        }
    }
    return matches;
};
getSourceZones.propTypes = {
    sourceId: PropTypes.number.isRequired,
    zones: PropTypes.array.isRequired,
};

const Add = ({
    cards,
    nextAvailableSource,
    sources,
    initSource,
}) => {
    if (cards.length < sources.length) {
        return(
        <div className="content">
            <div
                className="home-add-player-button"
                onClick={() => {
                    initSource(nextAvailableSource);
                }}
            >
                +
            </div>
        </div>
        )
    }
}
Add.propTypes = {
    cards: PropTypes.any.isRequired,
    nextAvailableSource: PropTypes.any.isRequired,
    sources: PropTypes.any.isRequired,
    initSource: PropTypes.any.isRequired,
};


const Preset = ({
    setPresetsModalOpen,
}) => {
    return (
        <div
            className="home-presets-button"
            onClick={() => setPresetsModalOpen(true)}
        >
    Presets
        </div>
    );
};
Preset.propTypes = {
    setPresetsModalOpen: PropTypes.any.isRequired,
};

const Home = () => {
    const sources = useStatusStore((s) => s.status.sources);
    const is_streamer = useStatusStore((s) => s.status.info.is_streamer);
    const clearSourceZones = useStatusStore((s) => s.clearSourceZones);
    const [zonesModalOpen, setZonesModalOpen] = React.useState(false);
    const [streamsModalOpen, setStreamsModalOpen] = React.useState(false);
    const [presetsModalOpen, setPresetsModalOpen] = React.useState(false);
    const [streamerOutputModalOpen, setStreamerOutputModalOpen] = React.useState(false);

    let nextAvailableSource = null;
    let cards = [];

    // create shallow copy and reverse before traversal so that the lowest
    // numbered available source will be the next available source
    sources.slice().reverse().forEach((source, i) => {
        if (
            source.input.toUpperCase() != "NONE" &&
            source.input != "" &&
            source.input != "local"
        ) {
            cards.unshift(
                <Grid style={{height: "40vh"}} className="grid-content" item xs={12} sm={12} md={12} lg={6} xl={6}>
                    <PlayerCardFb key={i} sourceId={source.id} />
                </Grid>
        );
        } else {
            nextAvailableSource = source.id;
        }
    });

    const initSource = (sourceId) => {
    // clear source zones for a source (on client and server)
        clearSourceZones(sourceId);

        // open first modal
        setStreamsModalOpen(true);
    };

    return (
        <div className="home-outer">
            <Grid container spacing={2} justifyContent={"space-around"}>
                {cards}
                <Grid className="grid-content" item xs={12} sm={12} md={12} lg={6} xl={6}>
                    <Add
                        cards={cards}
                        nextAvailableSource={nextAvailableSource}
                        sources={sources}
                        initSource={initSource}
                    />
                </Grid>
            </Grid>
            <Preset
                setPresetsModalOpen={setPresetsModalOpen}
            />

            {zonesModalOpen && (
                <ZonesModal
                    sourceId={nextAvailableSource}
                    loadZonesGroups={false}
                    // on apply, we want to call
                    onApply={executeApplyAction}
                    onClose={() => setZonesModalOpen(false)}
                />
            )}
            {streamerOutputModalOpen && (
                <StreamerOutputModal
                    sourceId={nextAvailableSource}
                    onApply={executeApplyAction}
                    onClose={() => setStreamerOutputModalOpen(false)}
                />
            )}

            {streamsModalOpen && (
                <StreamsModal
                    sourceId={nextAvailableSource}
                    applyImmediately={false}
                    onApply={() => {is_streamer ? setStreamerOutputModalOpen(true) : setZonesModalOpen(true)}}
                    onClose={() => setStreamsModalOpen(false)}
                />
            )}
            {presetsModalOpen && (
                <PresetsModal onClose={() => setPresetsModalOpen(false)} />
            )}
        </div>
    );
};

export default Home;
