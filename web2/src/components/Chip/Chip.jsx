import React from "react";

import PropTypes from "prop-types";
import "./Chip.scss";
import StopProp from "@/components/StopProp/StopProp";

const Chip = ({ children, onClick }) => {
    return (
        <StopProp>
            <div className="chip" onClick={onClick}>
                {children}
            </div>
        </StopProp>
    );
};
Chip.propTypes = {
    children: PropTypes.any.isRequired,
    onClick: PropTypes.func.isRequired,
};

export default Chip;
