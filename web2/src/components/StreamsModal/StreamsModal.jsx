import React from "react";
import "./StreamsModal.scss";
import Modal from "../Modal/Modal";
import Card from "../Card/Card";
// import StreamBadge from "../StreamBadge/StreamBadge";
import { useStatusStore } from "@/App";

import PropTypes from "prop-types";

const StreamsModal = ({ sourceId, setStreamModalOpen }) => {

    const streams = useStatusStore((state) => state.status.streams);

    const setStream = (streamId) => {
        setStreamModalOpen(false);

        fetch(`/api/sources/${sourceId}`, {
            method: "PATCH",
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({ input: `stream=${streamId}` }),
        });
    };


    let streamsList = [];

    for (const stream of streams) {
        streamsList.push(
            <div className="streams-modal-list-item" onClick={()=>{setStream(stream.id);}} key={stream.id}>
                {`${stream.name} - ${stream.type}`}
            </div>
        );
    }

    return(
        <Modal className="streams-modal">
            <Card className="streams-modal-card">
                <div className="streams-modal-header">
          Select Stream
                </div>
                <div className="streams-modal-body">
                    {streamsList}
                </div>
            </Card>
        </Modal>
    );
};
StreamsModal.propTypes = {
    sourceId: PropTypes.any.isRequired,
    setStreamModalOpen: PropTypes.func.isRequired,
};

export default StreamsModal;
