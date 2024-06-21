
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import ConfigModal from './ConfigTemplates/ConfigModal';

export default function ConfigDownload(){
    const [file, setFile] = React.useState([]);
    const [filePicked, setFilePicked] = React.useState(false);
    const [modalOpen, setModalOpen] = React.useState(false);

    const UploadConfig = () => {
        return fetch("/api/load", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(file),
        });
    };

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
                successText={"Config uploaded successfully!"}
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
        </>
    )
};
