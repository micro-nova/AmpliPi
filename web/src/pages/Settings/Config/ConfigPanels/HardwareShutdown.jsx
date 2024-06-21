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
        const { onClick } = props;
        return(
            <Button onClick={onClick}>Shutdown</Button>
        )
    }

    return(
        <ConfigPanel
            title={"Hardware Shutdown"}
            subheader={"Trigger a shutdown of the Raspberry Pi-based controller"}
            handler={HWShutdown}
            Contents={Contents}
            modalBody={"This will shut the unit off. It will need to be physically accessed to be turned back on."}
            successText={"Hardware shut down successfully!"} // You're never going to see this but it's required so eh
        />
    )
}
