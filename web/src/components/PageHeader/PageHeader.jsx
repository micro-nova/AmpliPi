import React from "react";
import "./PageHeader.scss";
import CloseIcon from "@mui/icons-material/Close";

import PropTypes from "prop-types";

const PageHeader = ({ title, onClose }) => {
    return (
        <div className="page-header">
            <div className="page-header-title">{title}</div>
            <div className="page-header-close" onClick={onClose}>
                <CloseIcon fontSize="inherit"></CloseIcon>
            </div>
        </div>
    );
};
PageHeader.propTypes = {
    title: PropTypes.string.isRequired,
    onClose: PropTypes.func.isRequired,
};

export default PageHeader;
