import React from "react";
import PropTypes from "prop-types";
import PageHeader from "@/components/PageHeader/PageHeader";
import "./Streams.scss";
import "../PageBody.scss";
import { useStatusStore } from "@/App.jsx";
import StreamModal from "../../../components/StreamModal/StreamModal";
import Fab from "@mui/material/Fab";
import AddIcon from "@mui/icons-material/Add";
import TypeSelectModal from "../../../components/TypeSelectModal/TypeSelectModal";
import StreamTemplates from "./StreamTemplates.json";
import { getIcon } from "@/utils/getIcon";
import List from "@mui/material/List/List";
import ListItem from "@mui/material/ListItem";
import Divider from "@mui/material/Divider";

const initEmptyStream = (type) => {
    const streamTemplate = StreamTemplates.filter((t) => t.type === type)[0];
    let stream = { type: type, disabled: false };
    streamTemplate.fields.forEach((field) => {
        stream[field.name] = field.default;
    });
    return stream;
};

const makeNewStream = (stream) => {
    return fetch("/api/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(stream),
    });
};

const StreamListItem = ({ stream }) => {
    const [showModal, setShowModal] = React.useState(false);
    const icon = getIcon(stream.type);
    return (
        <>
            <ListItem
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
                    />
                )}
            </ListItem>
            <Divider component="li" />
        </>
    );
};
StreamListItem.propTypes = {
    stream: PropTypes.any.isRequired,
};

const Streams = ({ onClose }) => {
    const streams = useStatusStore((state) => state.status.streams);
    const [showModal, setShowModal] = React.useState(false);
    const [showSelect, setShowSelect] = React.useState(false);
    const [selectedType, setSelectedType] = React.useState("");

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

            {showSelect && (
                <TypeSelectModal
                    onClose={() => {
                        setShowSelect(false);
                    }}
                    onSelect={(type) => {
                        setSelectedType(type);
                        setShowSelect(false);
                        setShowModal(true);
                    }}
                />
            )}
            {showModal && (
                <StreamModal
                    stream={initEmptyStream(selectedType)}
                    apply={makeNewStream}
                    onClose={() => {
                        setShowModal(false);
                    }}
                />
            )}
        </div>
    );
};
Streams.propTypes = {
    onClose: PropTypes.func.isRequired,
};

export default Streams;
