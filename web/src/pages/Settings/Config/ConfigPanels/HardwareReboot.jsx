import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';

export default function HardwareReboot() {
    const [modalOpen, setModalOpen] = React.useState(false);

    const HWReboot = () => {
        const response = fetch("/api/reboot", { method: "POST" });
        return response;
    };

    return(
        <>
            <ConfigPanel
                title={"Hardware Reboot"}
                subheader={"Reboots the Raspberry Pi-based controller"}
                successText={"Hardware rebooted successfully!"}
            >
                <Button onClick={() => {setModalOpen(true);}}>Reboot</Button>
            </ConfigPanel>

            <ConfigModal
                body={"This will reboot the CPU, which will take some time during which amplipi will not be able to play audio."}
                confirm={() => {HWReboot();}}
                open={modalOpen}
                setOpen={setModalOpen}
            />
        </>
    )
}
