
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';

export default function ConfigDownload(){
    const [file, setFile] = React.useState([]);
    const [filePicked, setFilePicked] = React.useState(false);

    function Base(props) {
        const { children } = props;
        return(
            <div>
                Upload Config
                <div className="config-desc">
                    {"Uploads the selected configuration file."}
                </div>
                {children}
            </div>
        )
    }

    const UploadConfig = () => {
        return fetch("/api/load", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(file),
        });
    };

    function Contents(props) {
        const { useFunction } = props;


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
            <div>
                <input
                    type="file"
                    accept=".json,application/json"
                    onChange={onChange}
                />
                <Button disabled={!filePicked} onClick={useFunction}>
                    Upload
                </Button>
            </div>
        )
    }

    const title = "Upload Config";
    const body = "replace the previous config, ensure you've downloaded the current config if you wish to keep it!";
    return(
        <ConfigPanel Base={Base} handler={UploadConfig} Contents={Contents} modalTitle={title} modalBody={body} />
    )
};
