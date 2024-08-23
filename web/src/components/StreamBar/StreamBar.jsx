import React from "react";
import "./StreamBar.scss";

import { useStatusStore } from "@/App.jsx";
import { getIcon } from "@/utils/getIcon";

import PropTypes from "prop-types";
import MetadataMarquee from "../CustomMarquee/MetadataMarquee";

const StreamBar = ({ sourceId, onClick }) => {
    const nameRef = React.useRef(null);
    const nametype = useStatusStore(
        (state) => state.status.sources[sourceId].info.name
    ).split(" - ");
    const type = nametype[1];
    const name = nametype[0];

    const icon = getIcon(type);
    //TODO: populate this with icons or add endpoint to get icons
    // code will be shared with StreamBadge, should be put somewhere else and imported
    return (
        <div onClick={onClick} className="stream-bar">
            <div className="stream-bar-name" ref={nameRef}><MetadataMarquee children={name} containerRef={nameRef} /></div>
            <img src={icon} className="stream-bar-icon" alt="stream icon" />
        </div>
    );
};
StreamBar.propTypes = {
    sourceId: PropTypes.number.isRequired,
    onClick: PropTypes.func,
};
StreamBar.defaultTypes = {
  onClick: () => {}
};

export default StreamBar;
