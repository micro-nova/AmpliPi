import React from "react";
import "./RectangularAddButton.scss"

import PropTypes from "prop-types";

export default function RectangularAddButton({onClick}){
    return(
        <div
            className="rectangular-add-button"
            onClick={onClick}
        >
            +
        </div>
    )
}
RectangularAddButton.propTypes = {
    onClick: PropTypes.func.isRequired,
};
