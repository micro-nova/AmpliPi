import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';
import StatusBar from './ConfigTemplates/StatusBar.jsx';

export default function HardwareReboot() {
    const [modalOpen, setModalOpen] = React.useState(false);
    const [loading, setLoading] = React.useState(false);
    const [response, setResponse] = React.useState(null);

    async function HWReboot(){
        setLoading(true);
        const resp = await fetch("/api/reboot", { method: "POST" });
        setResponse(resp);
        setLoading(false);
    };

    return(
        <>
            <ConfigPanel
                title={"Hardware Reboot"}
                subheader={"Reboots the Raspberry Pi-based controller"}
                loading={loading}
            >
                <Button onClick={() => {setModalOpen(true);}}>Reboot</Button>
            </ConfigPanel>

            <ConfigModal
                body={"This will reboot the CPU, which will take some time during which amplipi will not be able to play audio."}
                onApply={() => {HWReboot();}}
                open={modalOpen}
                setOpen={setModalOpen}
            />
            <StatusBar
                successText={"Hardware rebooted successfully!"}
                response={response}
            />
        </>
    )
}
