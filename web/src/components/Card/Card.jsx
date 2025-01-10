
import React from "react";
import "./Card.scss";

import PropTypes from "prop-types";

// card is a custom container with rounded corners.
// backgroundImage can be assigned, which is used for PlayerCardFb
const Card = ({
    backgroundImage,
    children,
    className,
    selected,
    selectable,
    onClick,

    secondary,
}) => {
    const cName = `card ${className} ${selectable && !selected ? "selectable" : ""} ${selected ? "selected" : ""} ${secondary ? "secondary" : "primary"}`
    const onClickFun = onClick === null ? () => {} : onClick;
    const topTransparency = selected ? 0.25 : 0.4;
    const bottomTransparency = selected ? 0.25 : 0.9;

    const backgroundSize =
    backgroundImage !== null && backgroundImage.includes("static/imgs/")
        ? "contain"
        : "cover";

    if (backgroundImage !== null) {
        return (
            <div
                className={cName}
                onClick={onClickFun}
                style={{
                    backgroundImage: `linear-gradient(rgba(0, 0, 0, ${topTransparency}), rgba(0, 0, 0, ${bottomTransparency})), url('${backgroundImage}')`,
                    backgroundSize: `${backgroundSize}`,
                    backgroundPosition: "center",
                    backgroundRepeat: "no-repeat",
                }}
            >
                {children}
            </div>
        );
    }
    return <div className={cName}>{children}</div>;
};
Card.propTypes = {
    backgroundImage: PropTypes.any,
    children: PropTypes.any,
    className: PropTypes.string,
    selected: PropTypes.bool,
    selectable: PropTypes.bool,
    onClick: PropTypes.func,

    secondary: PropTypes.bool,
};

Card.defaultProps = {
    backgroundImage: null,
    className: "",
    selected: false,
    selectable: false,
    onClick: null,

    secondary: false,
};

export default Card;
