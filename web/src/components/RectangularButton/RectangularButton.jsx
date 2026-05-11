import React from "react";
import "./RectangularButton.scss"

import PropTypes from "prop-types";

export default function RectangularButton({onClick, large, label}){
    return(
        <div
            className={large ? "rectangular-button rectangular-button-large-font" : "rectangular-button rectangular-button-small-font"}
            onClick={onClick}
        >
            {label}
        </div>
    );
}
RectangularButton.propTypes = {
    onClick: PropTypes.func.isRequired,
    large: PropTypes.bool,
    label: PropTypes.string.isRequired
};
RectangularButton.defaultProps = {
    large: false,
};
