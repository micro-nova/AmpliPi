import React from "react";

import PropTypes from "prop-types";
import "./Chip.scss";
import StopProp from "@/components/StopProp/StopProp";

const Chip = ({ children, onClick, style }) => {
    return (
        <StopProp>
            <div className="chip" onClick={onClick} style={style}>
                {children}
            </div>
        </StopProp>
    );
};
Chip.propTypes = {
    children: PropTypes.any.isRequired,
    onClick: PropTypes.func,
    style: PropTypes.object,
};

export default Chip;
