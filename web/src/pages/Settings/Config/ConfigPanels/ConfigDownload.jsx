
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import DownloadConfig from './DownloadConfig';

export default function ConfigDownload(){
    function Contents(props) {
        const { onClick } = props;
        return(
            <Button onClick={onClick}>Download</Button>
        )
    }

    return(
        <ConfigPanel
            title={"Download Config"}
            subheader={"Downloads the current configuration."}
            handler={DownloadConfig}
            Contents={Contents}
            successText={"Config downloaded successfully!"}
        />
    )
};
