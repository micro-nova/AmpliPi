import React from "react";
import "./PresetsModal.scss";
import ModalCard from "@/components/ModalCard/ModalCard";
import { useStatusStore } from "@/App";
import { useState } from "react";
import List from "@/components/List/List";
import ListItem from "@/components/List/ListItem/ListItem";
import CreatePresetModal from "@/components/CreatePresetModal/CreatePresetModal";

import PropTypes from "prop-types";

const timeSince = (timeStamp) => {
    var now = new Date(),
        secondsPast = (now.getTime() - timeStamp) / 1000;
    if (secondsPast < 60) {
        return parseInt(secondsPast) + "s";
    }
    if (secondsPast < 3600) {
        return parseInt(secondsPast / 60) + "m";
    }
    if (secondsPast <= 86400) {
        return parseInt(secondsPast / 3600) + "h";
    }
    if (secondsPast > 86400) {
        let day = timeStamp.getDate();
        let month = timeStamp
            .toDateString()
            .match(/ [a-zA-Z]*/)[0]
            .replace(" ", "");
        let year =
      timeStamp.getFullYear() == now.getFullYear()
          ? ""
          : " " + timeStamp.getFullYear();
        return day + " " + month + year;
    }
};

const PresetItem = ({ index, onClick, presetState }) => {
    const preset = useStatusStore((state) => state.status.presets[index]);
    const name = preset.name;
    const last_used = timeSince(new Date(preset.last_used * 1000)); // js expects milliseconds from epoch
    // const last_used = 0

    // show checkmark if presetState is 'done'
    // show spinner if presetState is 'loading'
    return (
        <>
            <ListItem onClick={() => onClick(index)} columns={false}>
                <div className="preset-name-and-last-used">
                    <div>{name}</div>
                    <div className="preset-item-last-used">{last_used}</div>
                </div>

                {presetState === "done" && <div className="preset-item-icon">✓</div>}
                {presetState === "loading" && (
                    <div className="preset-item-icon">⏳</div>
                )}
            </ListItem>
        </>
    );
};
PresetItem.propTypes = {
    onClick: PropTypes.func.isRequired,
    index: PropTypes.number.isRequired,
    presetState: PropTypes.any.isRequired,
};

const PresetsModal = ({ onClose, onApply }) => {
    const presets = useStatusStore((state) => state.status.presets);
    const [presetStates, setPresetStates] = useState(
        presets.map((preset) => {if(preset){return false;}}) // Changed this line so that preset wouldn't go unused as per eslint
    );
    const setSystemState = useStatusStore((s) => s.setSystemState);
    const [createModalOpen, setCreateModalOpen] = React.useState(false);

    // resize presetStates (without overriding) if length changes
    if (presetStates.length > presets.length) {
        setPresetStates(presetStates.slice(0, presets.length));
    } else if (presetStates.length < presets.length) {
        setPresetStates([
            ...presetStates,
            ...Array(presets.length - presetStates.length).fill(false),
        ]);
    }

    const apply = (index) => {
        setPresetStates(
            presetStates.map((state, i) => (i === index ? "loading" : state))
        );
        const id = presets[index].id;
        fetch(`/api/presets/${id}/load`, {
            method: "POST",
            accept: "application/json",
        }).then(res => {
            if(res.ok){res.json().then(s => setSystemState(s))}
            setPresetStates(
                presetStates.map((state, i) => (i === index ? "done" : state))
            )
        }).catch(() =>
            setPresetStates(
                presetStates.map((state, i) => (i === index ? false : state))
            )
        );
        onClose();
    };

    const presetItems = presets.map((preset, index) => (
        <PresetItem
            key={index}
            index={index}
            onClick={apply}
            presetState={presetStates[index]}
        />
    ));

    return (
        <ModalCard
            className="presets-modal"
            onClose={onClose}
            buttons={[
                [ "Create Preset", () => {setCreateModalOpen(true);} ],
                [ "Cancel", onClose ]
            ]}
        >
            <div className="presets-modal-header">Select Preset</div>
            <div className="presets-modal-body">
                <List>{presetItems}</List>
                { createModalOpen && <CreatePresetModal onApply={onApply} onClose={() => {setCreateModalOpen(false); onClose();}} /> }
            </div>
        </ModalCard>
    );
};
PresetsModal.propTypes = {
    onClose: PropTypes.func.isRequired,
    onApply: PropTypes.func,
};
PresetsModal.defaultProps ={
    onApply: () => {}
};

export default PresetsModal;
