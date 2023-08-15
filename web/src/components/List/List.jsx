import React from "react";

import PropTypes from "prop-types";
import "./List.scss";

const List = ({ children }) => {
    return <div className="list-container">{children}</div>;
};
List.propTypes = {
    children: PropTypes.any.isRequired,
};

export default List;
