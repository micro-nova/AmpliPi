import React from "react";
import PropTypes from "prop-types";
import "./Zones.scss";
import "../PageBody.scss";
import { useStatusStore } from "@/App.jsx";
import PageHeader from "@/components/PageHeader/PageHeader";
import Speaker from "@mui/icons-material/Speaker";
import List from "@mui/material/List/List";
import Divider from "@mui/material/Divider";
import ListItemButton from "@mui/material/ListItemButton";

import ZoneModal from "./ZoneModal/ZoneModal";


const ZoneListItem = ({ zone }) => {
    const [showModal, setShowModal] = React.useState(false);
    return (
        <>
            <ListItemButton
                key={zone.id}
                onClick={() => setShowModal(true)}
                style={{fontSize: "2rem"}}
            >
                <div className="zones-zone-icon">
                    <Speaker fontSize="inherit" />
                </div>
                <div className="zones-zone-name">{zone.name}</div>
                {showModal && <ZoneModal
                    zone={zone}
                    onClose={() => {
                        setShowModal(false);
                    }}
                />}
            </ListItemButton>
            <Divider component="li" />
        </>
    );
};
ZoneListItem.propTypes = {
    zone: PropTypes.any.isRequired,
};

const Zones = ({ onClose }) => {
    const zones = useStatusStore((state) => state.status.zones);

    const listItems = zones.map((zone) => {
        return(
            <ZoneListItem zone={zone} />
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
