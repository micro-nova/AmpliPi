import React from "react";
import PropTypes from "prop-types";

import {
    TextField,
    FormControlLabel,
    Switch,
    Button,
} from "@mui/material";

import ModalCard from "@/components/ModalCard/ModalCard";

export default function ZoneModal(props) {
    const {
        zone,
        onClose,
    } = props;

    const [name, setName] = React.useState("");
    const [vol_max, setVolMax] = React.useState(0);
    const [vol_min, setVolMin] = React.useState(-80);
    const [disabled, setDisabled] = React.useState(false);

    const applyChanges = () => {
        fetch(`/api/zones/${zone.id}`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            body: JSON.stringify({
                name: name,
                vol_max: vol_max,
                vol_min: vol_min,
                disabled: disabled,
            }),
        });
    };

    return(
        <ModalCard
            onClose={onClose}
            header={zone.name}
            onAccept={applyChanges}
        >
            <div className="zone-content-container">
                <TextField
                    className="zones-input"
                    type="text"
                    label="Name"
                    value={name}
                    margin="dense"
                    onChange={(e) => {
                        setName(e.target.value);
                    }}
                />
                <TextField
                    className="zones-input"
                    type="text"
                    label="Max Volume"
                    value={vol_max}
                    margin="dense"
                    onChange={(e) => {
                        setVolMax(e.target.value);
                    }}
                />
                <TextField
                    className="zones-input"
                    type="text"
                    label="Min Volume"
                    value={vol_min}
                    margin="dense"
                    onChange={(e) => {
                        setVolMin(e.target.value);
                    }}
                />
                <FormControlLabel label="Disabled"
                    control={<Switch
                        className="zones-input"
                        type="checkbox"
                        label="Disabled"
                        checked={disabled}
                        onChange={(e) => {
                            setDisabled(e.target.checked);
                        }}
                    />}
                />
            </div>
        </ModalCard>
    )
};
ZoneModal.propTypes = {
    zone: PropTypes.any.isRequired,
    onClose: PropTypes.func.isRequired,
};
