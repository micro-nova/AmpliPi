import React from "react";
import "./Modal.scss";
import StopProp from "@/components/StopProp/StopProp";
import PropTypes from "prop-types";

const Modal = ({ children, className = "", onClose }) => {
    const [mouseDownOutside, setMouseDownOutside] = React.useState(false);
    return (
        <div
            className={`modal_container ${className}`}
            onMouseDown={(e) => {
                if (e.target === e.currentTarget) {
                    setMouseDownOutside(true);
                } else {
                    setMouseDownOutside(false);
                }
            }}
            onMouseUp={(e) => {
                if (mouseDownOutside && e.target === e.currentTarget) {
                    onClose();
                }
            }}
        >
            <StopProp>{children}</StopProp>
        </div>
    );
};
Modal.propTypes = {
    children: PropTypes.any,
    className: PropTypes.string,
    onClose: PropTypes.func.isRequired
};
Modal.defaultProps = {
    className: ""
};

export default Modal;
