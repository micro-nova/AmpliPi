import React from "react";

import Slider from "@mui/material/Slider";
import "./VolumeSlider.scss";
import VolumeMuteIcon from "@mui/icons-material/VolumeMute";
import VolumeDownIcon from "@mui/icons-material/VolumeDown";
import VolumeOffIcon from "@mui/icons-material/VolumeOff";
import VolumeUpIcon from "@mui/icons-material/VolumeUp";
import StopProp from "@/components/StopProp/StopProp";

import LockOpenOutlinedIcon from '@mui/icons-material/LockOpenOutlined';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';

import PropTypes from "prop-types";
import { IconButton } from "@mui/material";

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
const VolumeSlider = ({ vol, mute, lock, setVol, setMute, setLock, disabled }) => {
    return (
        <StopProp>
            <div className="volume-slider-container">
                <div
                    onClick={() => {
                        setLock(!lock);
                    }}
                    className="volume-slider-icon-container"
                >
                  {!lock && <IconButton><LockOpenOutlinedIcon /></IconButton>}
                  {lock && <IconButton><LockOutlinedIcon /></IconButton>}
                </div>
                <div
                    onClick={() => {
                        setMute(!mute);
                    }}
                    className="volume-slider-icon-container"
                >
                    <VolIcon vol={vol} mute={mute} />
                </div>
                <Slider
                    disabled={disabled || lock}
                    className="volume-slider"
                    min={0}
                    step={0.01}
                    max={1}
                    value={vol}
                    onChange={(_, val) => {
                        setVol(val);
                    }}
                    onChangeCommitted={(_, val) => {
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
    lock: PropTypes.bool,
    setVol: PropTypes.func.isRequired,
    setMute: PropTypes.func.isRequired,
    setLock: PropTypes.func,
    disabled: PropTypes.bool,
};
VolumeSlider.defaultProps = {
    lock: false,
    setLock: () => {},
    disabled: false,
};

export default VolumeSlider;
