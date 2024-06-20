
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';
import { IsMobileApp } from "@/utils/MobileApp";

export default function ConfigDownload(){
    const DownloadConfig = () => {
        if (IsMobileApp()) {
            alert("This feature is not available in the mobile app.");
            return;
        }
        const response = fetch("/api");
        response.then((res) => {res.json().then((json) => {
            const element = document.createElement("a");
            const d = new Date();
            const file = new Blob([JSON.stringify(json, undefined, 2)], {
                type: "application/json",
            });
            element.href = URL.createObjectURL(file);
            element.download = `amplipi-config-${d.toJSON()}.json`;
            document.body.appendChild(element);
            element.click();
            });
        });
        return response;
    };

    function Contents(props) {
        const { useFunction } = props;
        return(
            <Button onClick={useFunction}>Download</Button>
        )
    }

    const success = "Config downloaded successfully!";
    return(
        <ConfigPanel
            title={"Download Config"}
            subheader={"Downloads the current configuration."}
            handler={DownloadConfig}
            Contents={Contents}
            successText={success}
        />
    )
};
