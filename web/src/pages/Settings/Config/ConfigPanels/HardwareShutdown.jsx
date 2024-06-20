import React from 'react';
import "../Config.scss";
import ConfigPanel from "./ConfigPanel.jsx";
import Button from '@mui/material/Button/Button';

export default function HardwareShutdown() {
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

    return(
        <ConfigPanel
            title={"HW Shutdown"}
            subheader={"Trigger a shutdown of the Raspberry Pi-based controller"}
            handler={HWShutdown}
            Contents={Contents}
            modalBody={"This will shut the unit off. It will need to be physically accessed to turn it back on."}
            successText={"Hardware shut down successfully!"}
        />
    )
}
