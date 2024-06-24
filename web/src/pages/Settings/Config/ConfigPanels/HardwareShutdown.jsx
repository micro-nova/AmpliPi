import React from 'react';
import "../Config.scss";
import ConfigPanel from "./ConfigTemplates/ConfigPanel.jsx";
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';

export default function HardwareShutdown() {
    const [modalOpen, setModalOpen] = React.useState(false);
    const [loading, setLoading] = React.useState(false);

    async function HWShutdown(){
        setLoading(true);
        fetch("/api/shutdown", { method: "POST" });
        setLoading(false);
    };

    return(
        <>
            <ConfigPanel
                title={"Hardware Shutdown"}
                subheader={"Trigger a shutdown of the embedded linux controller"}
                loading={loading}
            >
                <Button onClick={() => {setModalOpen(true);}}>Shutdown</Button>
            </ConfigPanel>

            <ConfigModal
                body={"This will shut the unit off. It will need to be physically accessed to be turned back on."}
                onApply={() => {HWShutdown();}}
                open={modalOpen}
                setOpen={setModalOpen}
            />
        </>
    )
}
