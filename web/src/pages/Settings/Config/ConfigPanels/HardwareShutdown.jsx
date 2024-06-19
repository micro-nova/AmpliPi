import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';

export default function HardwareShutdown() {
    function Base(props) {
        const { children } = props;
        return(
            <div>
                HW Shutdown
                <div className="config-desc">
                    {"Trigger a shutdown of the Raspberry Pi-based controller"}
                </div>
                {children}
            </div>
        )
    }

    const HWShutdown = () => {
        const response = fetch("/api/shutdown", { method: "POST" });
        return response;
    };

    function Contents(props) {
        const { useFunction } = props;
        return(
            <Button onClick={useFunction}>Shutdown</Button>
        )
    }

    const title = "do a Hardware Shutdown";
    const body = "shut the unit off. It will need to be physically accessed to turn it back on.";
    const success = "Hardware shut down successfully!";
    return(
        <ConfigPanel Base={Base} handler={HWShutdown} Contents={Contents} modalTitle={title} modalBody={body} successText={success} />
    )
}
