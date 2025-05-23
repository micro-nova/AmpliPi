import React from "react";
import PropTypes from "prop-types";
import ModalCard from "@/components/ModalCard/ModalCard";
import { Select, MenuItem } from "@mui/material";
import "./GroupModal.scss";
import Checkbox from "@mui/material/Checkbox";
import ListItemText from "@mui/material/ListItemText";
import TextField from "@mui/material/TextField";

const getZoneNames = (zones, ids) => {
    return zones
        .filter((i) => {
            return ids.indexOf(i.id) > -1;
        })
        .map((i) => {
            return i.name;
        })
        .join(", ");
};

const GroupModal = ({ group, zones, onClose, del, apply }) => {
    const [groupName, setGroupName] = React.useState(group.name);
    const [groupZones, setGroupZones] = React.useState(group.zones);

    return (
        <ModalCard
            onClose={onClose}
            header="Edit Group"
            buttons={[
                [ "Confirm", () => { apply(groupName, groupZones); onClose(); } ],
                [ del ? "Delete" : "Cancel", () => { if (del) del(); onClose(); } ]
            ]}
        >
            <div className="group-input-title">Name</div>
            <TextField className="group-name-input"
                fullWidth
                type="text"
                value={groupName}
                onChange={(e) => {
                    setGroupName(e.target.value);
                }}
            />
            <div className="group-input-title">Zones</div>
            <Select
                className="group-multi"
                multiple
                fullWidth
                defaultValue={groupZones}
                renderValue={(selected) => getZoneNames(zones, selected)}
                onChange={(e) => {
                    setGroupZones(e.target.value);
                }}
                MenuProps={{
                    PaperProps: {
                        style: {
                            maxHeight: "30vh",
                            overflowY: "scroll",  // Ensure scrollbar is always visible (except on iOS because apple hates you)
                        },
                        sx: {
                            "::-webkit-scrollbar": {
                                    width: "5px",
                            },
                            "::-webkit-scrollbar-thumb": {
                                backgroundColor: "#aaa",
                                borderRadius: "10px",
                            },
                        },
                    },
                }}
            >
                {zones.map((zone) => {
                    return (
                        <MenuItem key={zone.id} value={zone.id}>
                            <Checkbox checked={groupZones.indexOf(zone.id) > -1} />
                            <ListItemText primary={zone.name} />
                        </MenuItem>
                    );
                })}
            </Select>
        </ModalCard>
    );
};
GroupModal.propTypes = {
    group: PropTypes.any.isRequired,
    zones: PropTypes.array.isRequired,
    onClose: PropTypes.func.isRequired,
    del: PropTypes.func.isRequired,
    apply: PropTypes.func.isRequired,
};

export default GroupModal;
