import React from 'react';
import "../Config.scss";
import ConfigPanel from "./ConfigTemplates/ConfigPanel.jsx";
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';

export default function HardwareShutdown() {
    const [modalOpen, setModalOpen] = React.useState(false);

    const HWShutdown = () => {
        const response = fetch("/api/shutdown", { method: "POST" });
        return response;
    };

    function Contents(props) {
        const { onClick } = props;
        return(
            <Button onClick={onClick}></Button>
        )
    }

    return(
        <>
            <ConfigPanel
                title={"Hardware Shutdown"}
                subheader={"Trigger a shutdown of the Raspberry Pi-based controller"}
                successText={"Hardware shut down successfully!"} // You're never going to see this but it's required so eh
            >
                <Button onClick={() => {setModalOpen(true);}}>Shutdown</Button>
            </ConfigPanel>

            <ConfigModal
                body={"This will shut the unit off. It will need to be physically accessed to be turned back on."}
                confirm={() => {HWShutdown();}}
                open={modalOpen}
                setOpen={setModalOpen}
            />
        </>
    )
}
