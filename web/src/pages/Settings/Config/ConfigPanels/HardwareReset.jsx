import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';

export default function HardwareReset() {

    function Base(props) {
        const { children } = props;
        return(
            <div>
                HW Reset
                <div className="config-desc">
                    {
                        "Resets the preamp hardware and controller software (does not reboot the Raspberry Pi-based controller)"
                    }
                </div>
                {children}
            </div>
        )
    }

    const HWReset = () => {
        const response = fetch("/api/reset", { method: "POST" });
        return response;
    };

    function Contents(props) {
        const { useFunction } = props;
        return(
            <Button onClick={useFunction}>Reset</Button>
        )
    }

    const title = "do a Hardware Reset";
    const body = "reset the preamp hardware and controller software. This will take some time, during which amplipi will not be able to play audio.";
    const success = "Hardware has been reset successfully!";
    return(
        <ConfigPanel Base={Base} handler={HWReset} Contents={Contents} modalTitle={title} modalBody={body} successText={success} />
    )
}
