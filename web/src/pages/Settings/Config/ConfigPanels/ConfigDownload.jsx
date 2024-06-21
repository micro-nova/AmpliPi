
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';

export default function ConfigDownload(){
    const [modalOpen, setModalOpen] = React.useState(false);

    return(
        <>
            <ConfigPanel
                title={"Download Config"}
                subheader={"Downloads the current configuration."}
                successText={"Config downloaded successfully!"}
            >
                <Button onClick={() => {setModalOpen(true);}}>Download</Button>
            </ConfigPanel>

            <ConfigModal
                body={"This will reset all settings to factory default, ensure you've downloaded your current config if you wish to keep it!"}
                confirm={() => {DownloadConfig();}}
                open={modalOpen}
                setOpen={setModalOpen}
            />
        </>
    )
};
