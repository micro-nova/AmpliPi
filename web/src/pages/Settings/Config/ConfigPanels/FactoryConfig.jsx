
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';

export default function FactoryConfig(){
    const [modalOpen, setModalOpen] = React.useState(false);

    const FactoryReset = () => {
        const response = fetch("/api/factory_reset", { method: "POST" });
        return response;
    };

    return(
        <>
            <ConfigPanel
                title={"Factory Config"}
                subheader={"Resets Amplipi to the factory default configuration. We recommend downloading the current configuration beforehand."}
                successText={"AmpliPi reset to factory settings successfully!"}
            >
                <Button onClick={() => {setModalOpen(true);}}>Reset</Button>
            </ConfigPanel>

            <ConfigModal
                body={"This will reset all settings to factory default, ensure you've downloaded your current config if you wish to keep it!"}
                confirm={() => {FactoryReset();}}
                open={modalOpen}
                setOpen={setModalOpen}
            />
        </>
    )
}
