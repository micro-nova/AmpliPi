import React from "react";
import "./StreamsModal.scss";
import ModalCard from "@/components/ModalCard/ModalCard";
import { useStatusStore, usePersistentStore } from "@/App";
import { getIcon } from "@/utils/getIcon";
import { setRcaSourceId } from "../ZonesModal/ZonesModal";
import { moveSourceContents, setSourceStream } from "@/utils/APIHelper";
import { setRcaStatus } from "../ZonesModal/ZonesModal";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Divider from "@mui/material/Divider";
import CreateStreamModal from "@/components/CreateStreamModal/CreateStreamModal";

import PropTypes from "prop-types";

let applyAction = null;
let setSelectedSource = null; // Must be provided from the context of StreamsModal due to how hooks work
let setAutoselectSource = null; // Must be provided from the context of StreamsModal due to how hooks work

export const executeApplyAction = async (customSourceId) => {
    if (applyAction !== null && setSelectedSource !== null && setAutoselectSource !== null) {
        const temp = applyAction;
        applyAction = null;

        // temp returns undefined if called when sources are loading, a loop is used to ensure we only accept loaded variables
        let ret = undefined;
        while(ret == undefined){
            ret = await temp(customSourceId);
        };
        let sliced = parseInt(String(ret.url).slice(-1));
        setSelectedSource(sliced);
        setAutoselectSource(false);
        return ret;
    }
};

const StreamsModal = ({
    sourceId,
    onApply,
    onClose,
    applyImmediately,
}) => {
    const streams = useStatusStore((state) => state.status.streams);
    const status = useStatusStore((state) => state.status);
    const playingStreamIds = status.sources.filter( (s) => s.input !== 'None').map( (s) => parseInt(s.input.replace('stream=', '')));
    const playingStreams = streams.filter( (s) => playingStreamIds.includes(s.id) );
    const [createModalOpen, setCreateModalOpen] = React.useState(false);
    let filteredStreams = streams.filter( (s) => !playingStreamIds.includes(s.id) && !s.disabled);

    // If there are any running bluetooth or FM streams, mark other instances as disabled - we do not (yet)
    // support more than 1 hardware device at a time.
    const anyPlayingFmOrBluetooth = playingStreams.filter( (s) => s.type === 'fmradio' || s.type === 'bluetooth');
    for(const running of anyPlayingFmOrBluetooth) {
      filteredStreams = filteredStreams.map( (s) => {
        // we clone because all members of `s` are constant
        const r = structuredClone(s);
        if(r.type == running.type) {
          r.disabled = true;
          r.name = `${s.name} (hw in use)`;
        }
        return r
      });
    }

    setSelectedSource = usePersistentStore((s) => s.setSelectedSource);
    setAutoselectSource = usePersistentStore((s) => s.setAutoselectSource);

    const setStream = (stream) => {
        const streamId = stream.id;
        let currentSourceId = sourceId;
        // RCA can only be used on its associated source, so swap if necessary
        const moveSource = stream.type === "rca" && stream.index != sourceId;
        if (moveSource) {
            currentSourceId = stream.index;
            // notify ZonesModal that we are using a different sourceId
            setRcaSourceId(currentSourceId);
            // move whatever is here to the original source
        }

        const apply = (customSourceId) => {
            if (moveSource) {
                // move then set new stream
                const statusModified = JSON.parse(JSON.stringify(status));
                return moveSourceContents(status, currentSourceId, sourceId).then(
                    () => {
                        statusModified.zones.forEach((z) => {
                            if (z.source_id === currentSourceId) {
                                z.source_id = sourceId;
                            }
                        });
                        setRcaStatus(statusModified);
                        console.log(`move source. streamId: ${streamId}`);
                        return setSourceStream(currentSourceId, streamId);
                    }
                );
            } else if (typeof customSourceId == "number") { // 0 is falsy, but a valid index
                console.log(`setting custom source. streamId: ${streamId}, customSourceId: ${customSourceId}`);
                return setSourceStream(customSourceId, streamId);
            } else {
                // just set new stream
                console.log(`not move source. streamId: ${streamId}, sourceId: ${sourceId}`);
                return setSourceStream(sourceId, streamId);
            }
        };

        if (applyImmediately) {
            apply();
        } else {
            applyAction = apply;
        }
    };

    let streamsList = [];

    for (const stream of filteredStreams) {
        const icon = getIcon(stream.type);
        streamsList.push(
            <ListItemButton
                key={stream.id}
                disabled={stream.disabled}
                onClick={() => {
                    setStream(stream);
                    onApply();
                    onClose();
                }}
            >
                <img src={icon} className="streams-modal-icon" alt="stream icon" />
                <ListItemText className="streams-modal-item-text" primary={stream.name} />
            </ListItemButton>
        );
        streamsList.push(<Divider aria-hidden="true" />);
    }

    return (
        <ModalCard
            header="Select Stream"
            onClose={onClose}
            buttons={[
                ["Create Stream", () => {setCreateModalOpen(true);} ],
                ["Cancel", onClose ]
            ]}
            >
            <List>
                {streamsList}
            </List>
            <CreateStreamModal showSelect={createModalOpen} onClose={() => {setCreateModalOpen(false);}} />
        </ModalCard>
    );
};
StreamsModal.propTypes = {
    sourceId: PropTypes.number.isRequired,
    onApply: PropTypes.func,
    onClose: PropTypes.func.isRequired,
    applyImmediately: PropTypes.bool,
};
StreamsModal.defaultProps = {
    onApply: () => {},
    applyImmediately: true,
};

export default StreamsModal;
