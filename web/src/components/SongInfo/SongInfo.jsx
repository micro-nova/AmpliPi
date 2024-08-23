import React from "react";
import "./SongInfo.scss";
import { useStatusStore } from "@/App.jsx";
import MetadataMarquee from "../CustomMarquee/MetadataMarquee";

import PropTypes from "prop-types";

const SongInfo = ({
    sourceId,
    ...props
}) => {
    const info = useStatusStore((state) => state.status.sources[sourceId].info);
    const artistRef = React.useRef(null);
    const albumRef = React.useRef(null);
    const trackRef = React.useRef(null);

    return (
        <div className="song-info" {...props}>
            <div ref={artistRef} className={"artist-name"}>
                <MetadataMarquee children={info.artist} containerRef={artistRef} />
            </div>

            <div ref={albumRef} className={"album-name"}>
                <MetadataMarquee children={info.album} containerRef={albumRef} />
            </div>

            <div ref={trackRef} className={"track-name"}>
                <MetadataMarquee children={info.track} containerRef={trackRef} />
            </div>
        </div>
    );
};
SongInfo.propTypes = {
    sourceId: PropTypes.any.isRequired,
    props: PropTypes.any,
};

export default SongInfo;
