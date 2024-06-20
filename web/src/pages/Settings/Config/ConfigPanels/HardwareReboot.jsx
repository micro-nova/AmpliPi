import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';

export default function HardwareReboot() {
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

    return(
        <ConfigPanel
            title={"HW Reboot"}
            subheader={"Reboots the Raspberry Pi-based controller"}
            handler={HWReboot}
            Contents={Contents}
            modalBody={"This will reboot the CPU, which will take some time during which amplipi will not be able to play audio."}
            successText={"Hardware rebooted successfully!"}
        />
    )
}
