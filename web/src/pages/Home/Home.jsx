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

const AddSpacer = ({
    cards,
    nextAvailableSource,
    sources,
    initSource,
}) => {
    if (cards.length < sources.length) {
        const Add = () => {return(
        <Grid item xs={12} sm={12} md={6} lg={6} xl={6}>
            <div
                className="home-add-player-button"
                onClick={() => {
                    initSource(nextAvailableSource);
                }}
            >
                +
            </div>
        </Grid>
        )}

        if (((cards.length % 2) == 0) && window.innerWidth >= 900){ // The add component sometimes needs a spacer to ensure it doesn't go inbetween the two columns in the 2x2 grid mode
            const Spacer = () => {return(
                <Grid item xs={12} sm={12} md={6} lg={6} xl={6}>
                    <div className="container">
                    </div>
                </Grid>
            )}
            return ( <> <Add /> <Spacer /> </>)
        }

        return ( <Add /> )
    }
}
AddSpacer.propTypes = {
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


const DynaGrid = ({
    children
}) => {
    if(window.innerWidth < 900){
        return(
            <Grid className="grid-padding" container spacing={2} justifyContent={"space-around"}>
                {children}
            </Grid>
        )
    } else if(window.innerWidth >= 900){
        return(
            <Grid className="grid-padding" container spacing={3} justifyContent={"space-around"}>
                {children}
            </Grid>
        )
    }
}


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
                <Grid item xs={12} sm={12} md={6} lg={6} xl={6}>
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
            <DynaGrid className="grid-padding" container spacing={2} justifyContent={"space-around"}>
                {cards}
                <AddSpacer
                    cards={cards}
                    nextAvailableSource={nextAvailableSource}
                    sources={sources}
                    initSource={initSource}
                />
                <Grid item xs={12} sm={12} md={12} lg={12} xl={12}>
                    <Preset
                        setPresetsModalOpen={setPresetsModalOpen}
                    />
                </Grid>
            </DynaGrid>

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
