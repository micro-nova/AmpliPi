import React from "react";
import "./Card.scss";

import PropTypes from "prop-types";

const Card = ( {children, className, selected} ) => {

    return (
        <div className={`card ${className} ${selected ? " card card-selected" : ""}`}>
            {children}
        </div>
    );
};
Card.propTypes = {
    children: PropTypes.any,
    className: PropTypes.string,
    selected: PropTypes.bool,
};

Card.defaultProps = {
    selected: false,
};

export default Card;
