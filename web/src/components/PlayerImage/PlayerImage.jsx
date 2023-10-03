import React from "react";
import "./PlayerImage.scss";
import { useStatusStore } from "@/App";

import PropTypes from "prop-types";

const PlayerImage = ({ sourceId }) => {
    const img_url = useStatusStore((s) => s.status.sources[sourceId].info.img_url);
    return <img src={img_url} className="image" />;
};
PlayerImage.propTypes = {
    sourceId: PropTypes.any.isRequired,
};

export default PlayerImage;
