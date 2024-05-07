import React from "react";
import "./SongInfo.scss";
import { useStatusStore } from "@/App.jsx";
import CustomMarquee from "../CustomMarquee/CustomMarquee";

import PropTypes from "prop-types";

const SongInfo = ({
    sourceId,
}) => {
    const info = useStatusStore((state) => state.status.sources[sourceId].info);
    const artistRef = React.useRef(null);
    const albumRef = React.useRef(null);
    const trackRef = React.useRef(null);

    return (
        <div className="song-info song-info-marquee">
            <div ref={artistRef} className={"artist-name"}>
                <CustomMarquee children={info.artist} containerRef={artistRef} />
            </div>

            <div ref={albumRef} className={"album-name"}>
                <CustomMarquee children={info.album} containerRef={albumRef} />
            </div>

            <div ref={trackRef} className={"track-name"}>
                <CustomMarquee children={info.track} containerRef={trackRef} />
            </div>
        </div>
    );
};
SongInfo.propTypes = {
    sourceId: PropTypes.any.isRequired,
};

export default SongInfo;
