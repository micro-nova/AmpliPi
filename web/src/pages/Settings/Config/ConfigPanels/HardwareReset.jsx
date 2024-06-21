import React from 'react';
import "../Config.scss";
import ConfigPanel from "./ConfigTemplates/ConfigPanel.jsx";
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';

export default function HardwareReset() {
    const [modalOpen, setModalOpen] = React.useState(false);

    const HWReset = () => {
        const response = fetch("/api/reset", { method: "POST" });
        return response;
    };

    return(
        <>
            <ConfigPanel
                title={"Hardware Reset"}
                subheader={"Resets the preamp hardware and controller software (does not reboot the Raspberry Pi-based controller)"}
                successText={"Hardware has been reset successfully!"}
            >
                <Button onClick={() => {setModalOpen(true);}}>Reset</Button>
            </ConfigPanel>

            <ConfigModal
                body={"This will reset the preamp hardware and controller software. This will take some time, during which amplipi will not be able to play audio."}
                confirm={() => {HWReset();}}
                open={modalOpen}
                setOpen={setModalOpen}
            />
        </>
    )
}
