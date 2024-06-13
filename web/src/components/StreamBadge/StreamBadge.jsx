import React from "react";
import "./StreamBadge.scss";
import { useStatusStore } from "@/App.jsx";
import Chip from "@/components/Chip/Chip";
import { getIcon } from "@/utils/getIcon";

import PropTypes from "prop-types";

const StreamBadge = ({ sourceId, onClick }) => {
    const info = useStatusStore((s) => s.status.sources[sourceId].info);
    const name = info.name.split(" - ")[0];

    const icon = getIcon(info.type);

    return (
        <Chip onClick={onClick} style={{ maxWidth: "60vw" }}>
            <img src={icon} className="stream-badge-icon" alt="stream icon" />
            <div className="stream-badge-name">{name}</div>
        </Chip>
    );
};
StreamBadge.propTypes = {
    sourceId: PropTypes.any.isRequired,
    onClick: PropTypes.func.isRequired,
};

export default StreamBadge;
