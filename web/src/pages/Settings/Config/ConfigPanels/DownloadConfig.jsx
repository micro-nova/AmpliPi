
import React from 'react';
import "../Config.scss";
import ResponseBar from '@/components/StatusBars/ResponseBar.jsx';
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import ConfigDownload from './ConfigTemplates/ConfigDownload.jsx';

export default function DownloadConfig(){
    const [loading, setLoading] = React.useState(false);
    const [response, setResponse] = React.useState(null);

    async function handler(){
        setLoading(true);
        const resp = await ConfigDownload();
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
            <ResponseBar
                successText={"Config downloaded successfully!"}
                response={response}
            />
        </>
    )
}

