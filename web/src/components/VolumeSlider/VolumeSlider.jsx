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
const VolumeSlider = ({ vol, mute, setVol, setMute, disabled }) => {
    const touchStartX = React.useRef(0);
    const touchStartY = React.useRef(0);
    const isScrolling = React.useRef(false);

    const handleTouchStart = (e) => {
        const touch = e.touches[0];
        touchStartX.current = touch.clientX;
        touchStartY.current = touch.clientY;
        isScrolling.current = false;
    };

    const handleTouchMove = (e) => {
        const touch = e.touches[0];
        const diffX = touch.clientX - touchStartX.current;
        const diffY = touch.clientY - touchStartY.current;

        // Detect vertical drag, allow user to continue dragging within safe boundaries without needing to re-drag the slider
        isScrolling.current = (Math.abs(diffY) / Math.abs(diffX)) > 1.65;  // Equivalent to approximately 60 deg
    };

    const handleVolChange = (val, force = false) => {
        if (!isScrolling.current) {
            setVol(val, force);
        }
    }

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
                    disabled={disabled}
                    className="volume-slider"
                    min={0}
                    step={0.01}
                    max={1}
                    value={vol}
                    onTouchStart={handleTouchStart}
                    onTouchMove={handleTouchMove}
                    // https://github.com/mui/material-ui/issues/32737#issuecomment-2060439608
                    // ios does some weird emulation of mouse events from touch events, ignore those
                    onChange={(e, val) => {
                        if (isIOS() && e.type === "mousedown") {
                            return;
                        }
                        handleVolChange(val);
                    }}
                    onChangeCommitted={(e, val) => {
                        if (isIOS() && e.type === "mouseup") {
                            return;
                        }
                        handleVolChange(val, true);
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
