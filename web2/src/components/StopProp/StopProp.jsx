import React from "react";

import PropTypes from "prop-types";

const StopProp = ({ children }) => {
    return <div onClick={(e) => e.stopPropagation()}>{children}</div>;
};
StopProp.propTypes = {
    children: PropTypes.any.isRequired,
};

export default StopProp;
