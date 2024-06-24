import React from 'react';
import "../Config.scss";
import ConfigPanel from "./ConfigTemplates/ConfigPanel.jsx";
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';
import StatusBar from './ConfigTemplates/StatusBar.jsx';

export default function HardwareReset() {
    const [modalOpen, setModalOpen] = React.useState(false);
    const [loading, setLoading] = React.useState(false);
    const [response, setResponse] = React.useState(null);

    async function HWReset(){
        setLoading(true);
        const resp = await fetch("/api/reset", { method: "POST" });
        setResponse(resp);
        setLoading(false);
    };

    return(
        <>
            <ConfigPanel
                title={"Hardware Reset"}
                subheader={"Resets the preamp hardware and controller software (does not reboot the Raspberry Pi-based controller)"}
                loading={loading}
            >
                <Button onClick={() => {setModalOpen(true);}}>Reset</Button>
            </ConfigPanel>

            <ConfigModal
                body={"This will reset the preamp hardware and controller software. This will take some time, during which amplipi will not be able to play audio."}
                onApply={() => {HWReset();}}
                open={modalOpen}
                setOpen={setModalOpen}
            />
            <StatusBar
                successText={"Hardware has been reset successfully!"}
                response={response}
            />
        </>
    )
}
