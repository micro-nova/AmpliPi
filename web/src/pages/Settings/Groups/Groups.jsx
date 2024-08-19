import React from "react";
import PropTypes from "prop-types";
import PageHeader from "@/components/PageHeader/PageHeader";
import "../PageBody.scss";
import "./Groups.scss";
import { useStatusStore } from "@/App.jsx";
import { Fab } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import GroupModal from "./GroupModal/GroupModal";
import { SpeakerGroup } from "@mui/icons-material";
import List from "@mui/material/List/List";
import ListItemButton from "@mui/material/ListItemButton";
import Divider from "@mui/material/Divider";

const GroupListItem = ({ group, zones }) => {
    const [modalOpen, setModalOpen] = React.useState(false);

    const editGroup = (name, zones) => {
        fetch("/api/groups/" + group.id, {
            method: "PATCH",
            headers: { "Content-type": "application/json" },
            body: JSON.stringify({ name: name, zones: zones }),
        });
    };
    editGroup.propTypes = {
        name: PropTypes.any.isRequired,
        zones: PropTypes.any.isRequired,
    };

    const deleteGroup = () => {
        fetch("/api/groups/" + group.id, { method: "DELETE" });
    };

    return (
        <>
            <ListItemButton
            style={{fontSize: "2rem"}}
                onClick={() => {
                    setModalOpen(true);
                }}
            >
                <div className="groups-group-icon">
                    <SpeakerGroup fontSize="inherit" />
                </div>
                {group.name}
                {modalOpen && (
                    <GroupModal
                        group={group}
                        zones={zones}
                        onClose={() => {
                            setModalOpen(false);
                        }}
                        del={deleteGroup}
                        apply={editGroup}
                    />
                )}
            </ListItemButton>
            <Divider component="li" />
        </>
    );
};
GroupListItem.propTypes = {
    group: PropTypes.any.isRequired,
    zones: PropTypes.any.isRequired,
};

const addGroup = (name, zones) => {
    fetch("/api/group", {
        method: "POST",
        headers: { "Content-type": "application/json" },
        body: JSON.stringify({ name: name, zones: zones }),
    });
};

const Groups = ({ onClose }) => {
    const groups = useStatusStore((s) => s.status.groups);
    const zones = useStatusStore((s) => s.status.zones);
    const [modalOpen, setModalOpen] = React.useState(false);

    let groupsListItems = groups.map((group) => {
        return <GroupListItem key={group.id} group={group} zones={zones} />;
    });

    return (
        <div className="page-container">
            <PageHeader title="Groups" onClose={onClose} />
            <div className="page-body">
                <List>{groupsListItems}</List>
            </div>
            <div className="add-button">
                <Fab
                    onClick={() => {
                        setModalOpen(true);
                    }}
                >
                    <AddIcon />
                </Fab>
            </div>
            {modalOpen && (
                <GroupModal
                    group={{ name: "New Group", zones: [] }}
                    zones={zones}
                    onClose={() => setModalOpen(false)}
                    apply={addGroup}
                />
            )}
        </div>
    );
};
Groups.propTypes = {
    onClose: PropTypes.func.isRequired,
};

export default Groups;
