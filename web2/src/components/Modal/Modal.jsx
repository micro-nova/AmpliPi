import React from "react";

import "./Modal.scss";
import StopProp from "@/components/StopProp/StopProp";

import PropTypes from "prop-types";

const Modal = ({ children, className = "", onClose }) => {
  return (
    <div
      className={`modal_container ${className}`}
      onClick={(e) => {
        onClose()
        e.stopPropagation()
      }}
    >
      <StopProp>{children}</StopProp>
    </div>
  )
}
Modal.propTypes = {
    children: PropTypes.any,
    className: PropTypes.string,
    onClose: PropTypes.func.isRequired
};
Modal.defaultProps = {
    className: ""
}

export default Modal;
