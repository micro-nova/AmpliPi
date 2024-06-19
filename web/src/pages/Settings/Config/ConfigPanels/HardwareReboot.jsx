import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';

export default function HardwareReboot() {
    function Base(props) {
        const { children } = props;
        return(
            <div>
                HW Reboot
                <div className="config-desc">
                    {"Reboots the Raspberry Pi-based controller"}
                </div>
                {children}
            </div>
        )
    };

    const HWReboot = () => {
        const response = fetch("/api/reboot", { method: "POST" });
        return response;
    };

    function Contents(props) {
        const { useFunction } = props;
        return(
            <Button onClick={useFunction}>Reboot</Button>
        )
    }

    const title = "do a Hardware Reboot";
    const body = "reboot the CPU. This will take some time, during which amplipi will not be able to play audio.";
    const success = "Hardware rebooted successfully!";
    return(
        <ConfigPanel Base={Base} handler={HWReboot} Contents={Contents} modalTitle={title} modalBody={body} successText={success} />
    )
}
