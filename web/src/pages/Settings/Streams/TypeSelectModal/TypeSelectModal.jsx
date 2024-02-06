import React from "react";
import PropTypes from "prop-types";
import "./TypeSelectModal.scss";
import StreamTemplates from "../StreamTemplates.json";
import Modal from "@/components/Modal/Modal";
import Card from "@/components/Card/Card";
import { getIcon } from "@/utils/getIcon";
import ListItem from "@/components/List/ListItem/ListItem";
import { useStatusStore } from "@/App";

const TypeSelectModal = ({ onClose, onSelect }) => {
    const stream_types_available = useStatusStore((s) => s.status.info.stream_types_available);

    return (
        <>
            <Modal className="streams-modal" onClose={onClose}>
                <Card className="type-select-card">
                    <div className="type-select-title">Select A Stream Type</div>
                    <div>
                        {StreamTemplates
                            .filter((t) => !t.noCreate)
                            .filter((t) => stream_types_available.includes(t.type))
                            .map((t) => {
                                return (
                                    <ListItem
                                        key={t.type}
                                        name={t.name}
                                        onClick={() => {
                                            onSelect(t.type);
                                            onClose();
                                        }}
                                    >
                                        <img className="type-icon" src={getIcon(t.type)} />
                                    </ListItem>
                                );
                        })}
                    </div>
                </Card>
            </Modal>
        </>
    );
};
TypeSelectModal.propTypes = {
    onClose: PropTypes.func.isRequired,
    onSelect: PropTypes.func.isRequired,
};

export default TypeSelectModal;
