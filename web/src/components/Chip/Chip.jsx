import React from "react";

import PropTypes from "prop-types";
import "./Chip.scss";
import StopProp from "@/components/StopProp/StopProp";

const Chip = ({ children, onClick, style, shake}) => {
    let className = "chip"
    if(shake){
        className += " shake"
    }
    return (
        <StopProp>
            <div className={className} onClick={onClick} style={style}>
                {children}
            </div>
        </StopProp>
    );
};
Chip.propTypes = {
    children: PropTypes.any.isRequired,
    onClick: PropTypes.func,
    style: PropTypes.object,
    pulse: PropTypes.bool,
};

export default Chip;
