import React from "react";

import Slider from "@mui/material/Slider";
import "./VolumeSlider.scss";
import VolumeMuteIcon from "@mui/icons-material/VolumeMute";
import VolumeDownIcon from "@mui/icons-material/VolumeDown";
import VolumeOffIcon from "@mui/icons-material/VolumeOff";
import VolumeUpIcon from "@mui/icons-material/VolumeUp";
import StopProp from "@/components/StopProp/StopProp";
import { isIOS } from "@/utils/isIOS";

import PropTypes from "prop-types";

const VolIcon = ({ vol, mute }) => {
    if (mute) {
        return (
            <VolumeOffIcon
                fontSize="2rem"
                className="volume-slider-icon volume-slider-mute-icon"
            />
        );
    } else if (vol <= 0.2) {
        return <VolumeMuteIcon fontSize="2rem" className="volume-slider-icon" />;
    } else if (vol <= 0.5) {
        return <VolumeDownIcon fontSize="2rem" className="volume-slider-icon" />;
    } else {
        return <VolumeUpIcon fontSize="2rem" className="volume-slider-icon" />;
    }
};
VolIcon.propTypes = {
    vol: PropTypes.number.isRequired,
    mute: PropTypes.bool.isRequired,
};

// generic volume slider used by other volume sliders
const VolumeSlider = ({ vol, mute, setVol, setMute, disabled, ...params }) => {
    return (
        <StopProp>
            <div className="volume-slider-container">
                <div
                    onClick={() => {
                        setMute(!mute);
                    }}
                    className="volume-slider-icon-container"
                >
                    <VolIcon vol={vol} mute={mute} />
                </div>
                <Slider
                    {...params}
                    disabled={disabled}
                    className="volume-slider"
                    min={0}
                    step={0.01}
                    max={1}
                    value={vol}
                    // https://github.com/mui/material-ui/issues/32737#issuecomment-2060439608
                    // ios does some weird emulation of mouse events from touch events, ignore those
                    onChange={(e, val) => {
                        if(isIOS() && e.type === "mousedown"){
                            return;
                        }
                        setVol(val);
                    }}
                    onChangeCommitted={(e, val) => {
                        if(isIOS() && e.type === "mouseup"){
                            return;
                        }
                        setVol(val, true);
                    }}
                />
            </div>
        </StopProp>
    );
};
VolumeSlider.propTypes = {
    vol: PropTypes.number.isRequired,
    mute: PropTypes.bool.isRequired,
    setVol: PropTypes.func.isRequired,
    setMute: PropTypes.func.isRequired,
    disabled: PropTypes.bool,
};
VolumeSlider.defaultProps = {
    disabled: false,
};

export default VolumeSlider;
