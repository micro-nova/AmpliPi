
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import StatusBar from './ConfigTemplates/StatusBar.jsx';

export default function UploadConfig(){
    const [file, setFile] = React.useState([]);
    const [filePicked, setFilePicked] = React.useState(false);
    const [loading, setLoading] = React.useState(false);
    const [response, setResponse] = React.useState(null);

    async function ConfigUpload(){
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
                <Button disabled={!filePicked} onClick={() => {ConfigUpload();}}>
                    Upload
                </Button>
            </ConfigPanel>

            <StatusBar
                successText={"Config uploaded successfully!"}
                response={response}
            />
        </>
    )
};
