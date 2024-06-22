
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';
import StatusBar from './ConfigTemplates/StatusBar.jsx';

export default function ConfigDownload(){
    const [file, setFile] = React.useState([]);
    const [filePicked, setFilePicked] = React.useState(false);
    const [modalOpen, setModalOpen] = React.useState(false);
    const [loading, setLoading] = React.useState(false);
    const [response, setResponse] = React.useState(null);

    async function UploadConfig(){
        setLoading(true);
        const resp = await fetch("/api/load", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(file),
        });
        setResponse(resp);
        setLoading(false);
    }

    const onChange = (event) => {
        if (!event.target.files[0]) {
            setFilePicked(false);
            return;
        }
        event.target.files[0].text().then((text) => {
            setFile(JSON.parse(text));
        });
        setFilePicked(true);
    };

    return(
        <>
            <ConfigPanel
                title={"Upload Config"}
                subheader={"Uploads the selected configuration file."}
                loading={loading}
            >
                <input
                    type="file"
                    accept=".json,application/json"
                    onChange={onChange}
                />
                <Button disabled={!filePicked} onClick={() => {setModalOpen(true);}}>
                    Upload
                </Button>
            </ConfigPanel>

            <ConfigModal
                body={"This will replace the previous config, ensure you've downloaded the current config if you wish to keep it!"}
                confirm={() => {UploadConfig();}}
                open={modalOpen}
                setOpen={setModalOpen}
            />
            <StatusBar
                successText={"Config uploaded successfully!"}
                response={response}
            />
        </>
    )
};
