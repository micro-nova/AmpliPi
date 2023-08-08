import React from "react";
import PropTypes from "prop-types";
import PageHeader from "@/components/PageHeader/PageHeader";

const Sessions = ({ onClose }) => {
    return (
        <>
            <PageHeader title="Sessions" onClose={onClose} />
        </>
    );
};
Sessions.propTypes = {
    onClose: PropTypes.func.isRequired,
};

export default Sessions;
