
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';
import StatusBar from './ConfigTemplates/StatusBar.jsx';

export default function FactoryConfig(){
    const [modalOpen, setModalOpen] = React.useState(false);
    const [loading, setLoading] = React.useState(false);
    const [response, setResponse] = React.useState(null);

    async function FactoryReset(){
        setLoading(true);
        const resp = await fetch("/api/factory_reset", { method: "POST" });
        setResponse(resp);
        setLoading(false);
    };

    return(
        <>
            <ConfigPanel
                title={"Factory Config"}
                subheader={"Resets Amplipi to the factory default configuration. We recommend downloading the current configuration beforehand."}
                loading={loading}
            >
                <Button onClick={() => {setModalOpen(true);}}>Reset</Button>
            </ConfigPanel>

            <ConfigModal
                body={"This will reset all settings to factory default, ensure you've downloaded your current config if you wish to keep it!"}
                onApply={() => {FactoryReset();}}
                open={modalOpen}
                setOpen={setModalOpen}
            />
            <StatusBar
                successText={"AmpliPi reset to factory settings successfully!"}
                response={response}
            />
        </>
    )
}
