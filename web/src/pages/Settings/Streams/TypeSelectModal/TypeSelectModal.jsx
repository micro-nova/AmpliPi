import React from "react";
import PropTypes from "prop-types";
import "./TypeSelectModal.scss";
import StreamTemplates from "../StreamTemplates.json";
import Modal from "@/components/Modal/Modal";
import Card from "@/components/Card/Card";
import { getIcon } from "@/utils/getIcon";
import ListItem from "@/components/List/ListItem/ListItem";

const TypeSelectModal = ({ onClose, onSelect }) => {
    return (
        <>
            <Modal className="streams-modal" onClose={onClose}>
                <Card className="type-select-card">
                    <div className="type-select-title">Select A Stream Type</div>
                    <div>
                        {StreamTemplates.filter((t) => !t.noCreate).map((t) => {
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
