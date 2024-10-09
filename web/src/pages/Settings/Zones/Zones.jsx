import React from "react";
import PropTypes from "prop-types";
import "./Zones.scss";
import "../PageBody.scss";
import { useStatusStore } from "@/App.jsx";
import PageHeader from "@/components/PageHeader/PageHeader";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { Button } from "@mui/material";
import Speaker from "@mui/icons-material/Speaker";
import List from "@mui/material/List/List";
import ListItemButton from "@mui/material/ListItemButton";
import Divider from "@mui/material/Divider";
import TextField from "@mui/material/TextField";
import Switch from "@mui/material/Switch";
import FormControlLabel from "@mui/material/FormControlLabel";
import StatusBar from "@/components/StatusBars/StatusBar";

const ZoneListItem = ({ zone }) => {
    const [open, setOpen] = React.useState(false);
    const [name, setName] = React.useState(zone.name);
    const [vol_max, setVolMax] = React.useState(zone.vol_max);
    const [vol_min, setVolMin] = React.useState(zone.vol_min);
    const [disabled, setDisabled] = React.useState(zone.disabled);

    const [alertSuccess, setAlertSuccess] = React.useState(false);
    const [alertOpen, setAlertOpen] = React.useState(false);
    const [alertText, setAlertText] = React.useState("");

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
        }).then(resp => {
            if(resp.ok){
                setAlertText(`Zone ${zone.id} updated successfully!`);
                setAlertSuccess(true);
                setAlertOpen(true);
            } else {
                setAlertText(`Zone ${zone.id} update failed...`);
                setAlertSuccess(false);
                setAlertOpen(true);
            }
        });
    };

    return (
        <ListItemButton onClick={() => { if(!open) {setOpen(!open)} }}>
            <div className="zones-zone-column">
                <div className="zones-zone-row">
                    <div className="zones-zone-icon">
                        <Speaker fontSize="inherit" />
                    </div>
                    <div className="zones-zone-name">{zone.name}</div>
                    <div className="zones-zone-expand-button">
                        {open ? (
                            <KeyboardArrowUpIcon
                                className="zones-zone-expand-icon"
                                fontSize="inherit"
                                onClick={() => setOpen(!open)}
                            />
                        ) : (
                            <KeyboardArrowDownIcon
                                className="zones-zone-expand-icon"
                                fontSize="inherit"
                            />
                        )}
                    </div>
                </div>
                {open && (
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
                        <Button variant="contained" onClick={applyChanges}>Apply</Button>
                    </div>
                )}
            </div>
            <StatusBar
                open={alertOpen}
                onClose={() => {setAlertOpen(false);}}
                status={alertSuccess}
                text={alertText}
            />
        </ListItemButton>
    );
};
ZoneListItem.propTypes = {
    zone: PropTypes.any.isRequired,
};

const Zones = ({ onClose }) => {
    const zones = useStatusStore((state) => state.status.zones);

    const listItems = zones.map((zone) => {
        return(
            <>
                <ZoneListItem zone={zone} key={zone.id} />
                <Divider component="li" />
            </>
        );
    });

    return (
        <div className="page-container">
            <PageHeader title="Zones" onClose={onClose} />
            <div className="page-body">
                <List>{listItems}</List>
            </div>
        </div>
    );
};
Zones.propTypes = {
    onClose: PropTypes.func.isRequired,
};

export default Zones;
