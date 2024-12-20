import React from "react";

import PropTypes from "prop-types";

import "./ListItem.scss";

const ListItem = ({
    name,
    children,
    onClick,
    nameFontSize,
    footer,
    columns
}) => {
    return (
        <div
            className={columns ? "list-item-container columns" : "list-item-container"}
            onClick={onClick != undefined ? onClick : () => {}}
            style={{ cursor: onClick != undefined ? "pointer" : "default" }}
        >
            <div className="list-item-child">{children}</div>
            <div className="list-item-name" style={{ fontSize: nameFontSize }}>
                {name}
            </div>
            <div className="list-item-footer">
                {footer}
            </div>
        </div>
    );
};
ListItem.propTypes = {
    name: PropTypes.string.isRequired,
    children: PropTypes.any.isRequired,
    onClick: PropTypes.func.isRequired,
    nameFontSize: PropTypes.string.isRequired,
    footer: PropTypes.any,
    columns: PropTypes.bool,
};
ListItem.defaultProps = {
    onClick: undefined,
    nameFontSize: "2rem",
    columns: true,
};

export default ListItem;
