import React from "react";
import PropTypes from "prop-types";
import StreamTemplates from "./StreamTemplates.json";
import TypeSelectModal from "./TypeSelectModal/TypeSelectModal";
import StreamModal from "./StreamModal/StreamModal";

export default function CreateStreamModal({showSelect, onClose}) {
    // A wrapper for two modals so that their workflows can easily be placed wherever needed
    const [showCreate, setShowCreate] = React.useState(false);
    const [selectedType, setSelectedType] = React.useState("");

    const initEmptyStream = (type) => {
        const streamTemplate = StreamTemplates.filter((t) => t.type === type)[0];
        let stream = { type: type, disabled: false };
        streamTemplate.fields.forEach((field) => {
            stream[field.name] = field.default;
        });
        return stream;
    };

    return(
        <>
            {showSelect && (
                <TypeSelectModal
                    onClose={() => {
                        onClose();
                    }}
                    onSelect={(type) => {
                        setSelectedType(type);
                        onClose();
                        setShowCreate(true);
                    }}
                />
            )}
            {showCreate && (
                <StreamModal
                    stream={initEmptyStream(selectedType)}
                    onClose={() => {
                        setShowCreate(false);
                    }}
                />
            )}
        </>
    )
};
CreateStreamModal.propTypes = {
    showSelect: PropTypes.bool.isRequired,
    onClose: PropTypes.func.isRequired,
};
