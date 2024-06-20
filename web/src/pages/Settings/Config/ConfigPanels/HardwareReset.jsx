import React from 'react';
import "../Config.scss";
import ConfigPanel from "./ConfigPanel.jsx";
import Button from '@mui/material/Button/Button';

export default function HardwareReset() {
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

    return(
        <ConfigPanel
            title={"HW Reset"}
            subheader={"Resets the preamp hardware and controller software (does not reboot the Raspberry Pi-based controller)"}
            handler={HWReset}
            Contents={Contents}
            modalBody={"This will reset the preamp hardware and controller software. This will take some time, during which amplipi will not be able to play audio."}
            successText={"Hardware has been reset successfully!"}
        />
    )
}
