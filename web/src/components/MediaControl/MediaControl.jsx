
import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faStepBackward,
    faStepForward,
    faPause,
    faPlay,
    faStop,
    faThumbsDown,
    faThumbsUp,
} from "@fortawesome/free-solid-svg-icons";
import { curry } from "ramda";

import { useStatusStore } from "@/App.jsx";

import "./MediaControl.scss";

import PropTypes from "prop-types";

import "./MediaControl.scss";

const MediaControl = ({ selectedSource }) => {
    // const source = status.sources[selectedSource]
    const source = useStatusStore((s) => s.status.sources[selectedSource]);
    const meta = useStatusStore((s) => s.status.sources[selectedSource].info);

    const [invertRating, setInverse] = React.useState(false); // Stores the clicked state of a song, that way it can be set to have a green thumb if the like is clicked as that metadata won't update in the backend until the song is played again
    const [currentSong, setSong] = React.useState();

    React.useEffect(() => {
        if(currentSong != String(meta.track)){
            setInverse(false);
            setSong(String(meta.track));
        }
    }, [meta])

    const enabled = "media-control media-control-enabled";
    const disabled = "media-control media-control-disabled";
    const streamId = source.input.split("=")[1]; // TODO: what if this is rca? or is rca a stream now

    const setSourceState = curry(useStatusStore((s) => s.setSourceState))(
        selectedSource
    );

    // const setSourceState = (state) => {setState(selectedSource, state)}

    const playing = source.info.state.includes("playing");
    const isSupported = (cmd) => source.info.supported_cmds.includes(cmd);
    const postCommand = (cmd) => {
        fetch(`/api/streams/${streamId}/${cmd}`, {
            method: "POST",
            headers: {
                "Content-type": "application/json",
            },
        });
    };

    const Center = (() => {
        if (playing) {
            if (isSupported("pause")) {
                return (
                    <FontAwesomeIcon
                        icon={faPause}
                        className={enabled}
                        onClick={() => {
                            postCommand("pause");
                            setSourceState("paused");
                        }}
                    />
                );
            } else if (isSupported("stop")) {
                return (
                    <FontAwesomeIcon
                        icon={faStop}
                        className={enabled}
                        onClick={() => {
                            postCommand("stop");
                            setSourceState("stopped");
                        }}
                    />
                );
            } else {
                return <FontAwesomeIcon icon={faStop} className={disabled} />;
            }
        } else {
            if (isSupported("play")) {
                return (
                    <FontAwesomeIcon
                        icon={faPlay}
                        className={enabled}
                        onClick={() => {
                            postCommand("play");
                            setSourceState("playing");
                        }}
                    />
                );
            } else {
                return <FontAwesomeIcon icon={faPlay} className={disabled} />;
            }
        }
    })();

    const cmdToClassName = (cmd) => (isSupported(cmd) ? enabled : disabled);

    const Backward = (
        <FontAwesomeIcon
            icon={faStepBackward}
            className={cmdToClassName("prev")}
            onClick={() => postCommand("prev")}
        />
    );
    const Forward = (
        <FontAwesomeIcon
            icon={faStepForward}
            className={cmdToClassName("next")}
            onClick={() => postCommand("next")}
        />
    );

    function Ban() {
        if(isSupported("ban")){
            let thumbColor;
            if(meta.rating == 2){
                thumbColor = "#FF0000";
            } else {
                thumbColor = "#FFFFFF";
            }
            return(
                <FontAwesomeIcon
                    style={{ color: thumbColor, transition: 'color 5s' }}
                    icon={faThumbsDown}
                    className={cmdToClassName("ban")}
                    onClick={() => {postCommand("ban");}}
                />
            )
        }
    }

    function Love() {
        if(isSupported("love")){
            let thumbColor;
            if(meta.rating != 1){
                if(invertRating){
                    thumbColor = "#00FF00";
                } else {
                    thumbColor = "#FFFFFF";
                }
            } else {
                if(invertRating){
                    thumbColor = "#FFFFFF";
                } else {
                    thumbColor = "#00FF00";
                }
            }
            return(
                <FontAwesomeIcon
                    style={{ color: thumbColor, transition: 'color 5s' }}
                    icon={faThumbsUp}
                    className={cmdToClassName("love")}
                    onClick={() => {postCommand("love"); setInverse(!invertRating);}}
                />
            )
        }
    }

    return (
        <div className="media-outer">
            <div className="media-inner">
                <Ban />
                {Backward}
                {Center}
                {Forward}
                <Love />
            </div>
        </div>
    );
};
MediaControl.propTypes = {
    selectedSource: PropTypes.any.isRequired,
};

export default MediaControl;
