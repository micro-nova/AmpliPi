import React from "react";
import PropTypes from "prop-types";
import PageHeader from "@/components/PageHeader/PageHeader";
import "./Streams.scss";
import "../PageBody.scss";
import { useStatusStore } from "@/App.jsx";
import CreateStreamModal from "@/components/CreateStreamModal/CreateStreamModal";
import Fab from "@mui/material/Fab";
import AddIcon from "@mui/icons-material/Add";
import { getIcon } from "@/utils/getIcon";
import List from "@mui/material/List/List";
import ListItemButton from "@mui/material/ListItemButton";
import Divider from "@mui/material/Divider";
import StreamModal from "@/components/CreateStreamModal/StreamModal/StreamModal";

const applyStreamChanges = (stream) => {
    return fetch(`/api/streams/${stream.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(stream),
    });
};

const deleteStream = (stream) => {
    fetch(`/api/streams/${stream.id}`, { method: "DELETE" });
};

const StreamListItem = ({ stream }) => {
    const [showModal, setShowModal] = React.useState(false);
    const icon = getIcon(stream.type);
    return (
        <>
            <ListItemButton
                key={stream.id}
                onClick={() => setShowModal(true)}
                style={{fontSize: "2rem"}}
            >
                <img src={icon} className="stream-modal-icon" alt="stream icon" />
                {stream.name}
                {showModal && (
                    <StreamModal
                        stream={stream}
                        onClose={() => {
                            setShowModal(false);
                        }}
                        apply={applyStreamChanges}
                        del={deleteStream}
                    />
                )}
            </ListItemButton>
            <Divider component="li" />
        </>
    );
};
StreamListItem.propTypes = {
    stream: PropTypes.any.isRequired,
};

const Streams = ({ onClose }) => {
    const streams = useStatusStore((state) => state.status.streams);
    const [showSelect, setShowSelect] = React.useState(false);

    return (
        <div className="page-container">
            <PageHeader title="Streams" onClose={onClose} />
            <div className="page-body">
                <List>
                    {streams.map((stream) => {
                        return <StreamListItem key={stream.id} stream={stream} />;
                    })}
                </List>
                <div className="add-button">
                    <Fab onClick={() => setShowSelect(true)}>
                        <AddIcon />
                    </Fab>
                </div>
            </div>
            <CreateStreamModal showSelect={showSelect} onClose={() => {setShowSelect(false);}} />
        </div>
    );
};
Streams.propTypes = {
    onClose: PropTypes.func.isRequired,
};

export default Streams;
