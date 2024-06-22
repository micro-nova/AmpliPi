
import React from 'react';
import "../Config.scss";
import StatusBar from './ConfigTemplates/StatusBar.jsx';
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import DownloadConfig from './DownloadConfig';

export default function ConfigDownload(){
    const [loading, setLoading] = React.useState(false);
    const [response, setResponse] = React.useState(null);

    async function handler(){
        setLoading(true);
        const resp = await DownloadConfig();
        setResponse(resp);
        setLoading(false);
    }

    return(
        <>
            <ConfigPanel
                title={"Download Config"}
                subheader={"Downloads the current configuration."}
                loading={loading}
            >
                <Button onClick={() => {handler();}}>Download</Button>
            </ConfigPanel>
            <StatusBar
                successText={"Config downloaded successfully!"}
                response={response}
            />
        </>
    )
}

