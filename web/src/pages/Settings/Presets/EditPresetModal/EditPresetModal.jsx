import React from "react";
import PropTypes from "prop-types";
import "./EditPresetModal.scss";
import ModalCard from "@/components/ModalCard/ModalCard.jsx";
import TextField from "@mui/material/TextField";

const EditPresetModal = ({ onClose, preset }) => {
    const [name, setName] = React.useState(preset.name);

    const editPreset = () => {
        const preset_copy = JSON.parse(JSON.stringify(preset));
        preset_copy.name = name;
        fetch(`/api/presets/${preset.id}`, {
            method: "PATCH",
            headers: { "Content-type": "application/json" },
            body: JSON.stringify(preset_copy),
        });
    };

    const deletePreset = () => {
        fetch(`/api/presets/${preset.id}`, { method: "DELETE" });
    };

    return (
        <ModalCard
            onClose={onClose}
            onDelete={() => {
                deletePreset();
                onClose();
            }}
            onAccept={() => {
                editPreset();
                onClose();
            }}
        >
            <div className="preset-name">Edit Preset</div>
            <div className="preset-name-input-container">
                <div>Name</div>
                <TextField
                    className="preset-name-input"
                    fullWidth
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />
            </div>
        </ModalCard>
    );
};
EditPresetModal.propTypes = {
    onClose: PropTypes.func.isRequired,
    preset: PropTypes.string.isRequired,
};

export default EditPresetModal;
