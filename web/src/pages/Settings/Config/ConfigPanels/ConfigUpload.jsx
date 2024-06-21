
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';

export default function ConfigDownload(){
    const [file, setFile] = React.useState([]);
    const [filePicked, setFilePicked] = React.useState(false);

    const UploadConfig = () => {
        return fetch("/api/load", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(file),
        });
    };

    function Contents(props) {
        const { onClick } = props;

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
                <input
                    type="file"
                    accept=".json,application/json"
                    onChange={onChange}
                />
                <Button disabled={!filePicked} onClick={onClick}>
                    Upload
                </Button>
            </>
        )
    }

    return(
        <ConfigPanel
            title={"Upload Config"}
            subheader={"Uploads the selected configuration file."}
            handler={UploadConfig}
            Contents={Contents}
            modalBody={"This will replace the previous config, ensure you've downloaded the current config if you wish to keep it!"}
            successText={"Config uploaded successfully!"}
        />
    )
};
