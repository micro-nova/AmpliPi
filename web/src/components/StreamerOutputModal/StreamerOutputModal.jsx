/* eslint-disable react/prop-types */
import React from "react";
import "./StreamerOutputModal.scss";
import ModalCard from "@/components/ModalCard/ModalCard";
import Checkbox from "@mui/material/Checkbox";
import { useState } from "react";
import { useStatusStore } from "@/App.jsx";
import SpeakerIcon from "@mui/icons-material/Speaker";
import SpeakerGroupIcon from "@mui/icons-material/SpeakerGroup";
import ListItem from "@/components/List/ListItem/ListItem.jsx";
import List from "@/components/List/List.jsx";

import PropTypes from "prop-types";

const LIST_ITEM_FONT_SIZE = "1.5rem";

const StreamerOutputModal = ({
    sourceId,
    onApply,
    onClose,
}) => {
    const outputs = useStatusStore((s) => s.status.sources);

    const StreamerOutputModalOutputItem = (props) => {
        const {
            output,
            // defaultSelected, commented out due to non-use
        } = props;
        return (
            <ListItem
                name={output.name}
                nameFontSize={LIST_ITEM_FONT_SIZE}
                onClick={() => {
                    sourceId.current = output.id;
                    onApply();
                    onClose();
                }}
                key={output.id}
            >
                <div className="zone-icon">
                    <SpeakerIcon />
                </div>
            </ListItem>
        );
    };
    StreamerOutputModalOutputItem.propTypes = {
        output: PropTypes.any.isRequired,
        // defaultSelected: PropTypes.bool,
        //checked: PropTypes.bool.isRequired,
    };
    // StreamerOutputModalZoneItem.defaultProps = {
    //     defaultSelected: false,
    // };

    const setOutput = (output) => {
        console.log(output);
        fetch(`/api/sources/${output.id}`, {
            method: "PATCH",
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({
                input: `stream=${streamId}`,
            }),
        });
    };

    const outputItems = outputs.map((output) => {
        return StreamerOutputModalOutputItem({
            output: output,
        });
    });

    return (
        <ModalCard
            onClose={onClose}
            onCancel={onClose}
            header="Select Outputs"
        >
            <List>
                {outputItems}
            </List>
        </ModalCard>
    );
};
StreamerOutputModal.propTypes = {
    sourceId: PropTypes.object.isRequired,
    onApply: PropTypes.func.isRequired,
    onClose: PropTypes.func.isRequired,
};
StreamerOutputModal.defaultProps = {
    onApply: null,
    onClose: () => {},
};

export default StreamerOutputModal;
