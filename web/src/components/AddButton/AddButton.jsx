import React from "react";
import "./AddButton.scss";

import PropTypes from "prop-types";

export default function AddButton(props){
    const {
        onClick
    } = props
    return(
        <div className="add-button-component" onClick={onClick} >
            +
        </div>
    )
};
AddButton.propTypes = {
    onClick: PropTypes.func.isRequired,
};
