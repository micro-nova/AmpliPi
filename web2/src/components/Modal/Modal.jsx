import React from "react";

import "./Modal.scss";

import PropTypes from "prop-types";

const Modal = ({children, className}) => {
    return (
        <div className={`modal_container ${className}`}>
            {children}
        </div>
    );
};
Modal.propTypes = {
    children: PropTypes.any,
    className: PropTypes.string,
};

export default Modal;
