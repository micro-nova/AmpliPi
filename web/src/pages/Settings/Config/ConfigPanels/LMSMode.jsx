import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import { useStatusStore } from "@/App.jsx";
import Switch from '@mui/material/Switch/Switch';
import { IsMobileApp } from "@/utils/MobileApp";

export default function LMSMode() {

    function DownloadConfig() {
        if (IsMobileApp()) {
            alert("This feature is not available in the mobile app.");
            return;
        }
        fetch("/api").then((response) => {
            response.json().then((json) => {
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
    };

    function Base(props) {
        const { children } = props;
        return(
            <div>
                Lyrion Media Server (LMS) Mode
                <div className="config-desc">
                    {
                        "Toggles LMS Mode on or off. LMS is useful for piggy-backing off integrations AmpliPi does not have natively. This will wipe out the current config! As a result, it downloads the current config before proceeding with LMS mode."
                    }
                </div>
                {children}
            </div>
        )
    }

    const LMSModeHandler = () => {
        DownloadConfig();
        const response = fetch("/api/lms_mode", { method: "POST" });
        return response;
    };

    function Contents(props) {
        const { useFunction } = props;
        const lmsMode = useStatusStore((s) => s.status.info.lms_mode);
        return(
            <Switch
                checked={lmsMode}
                onChange={useFunction}
                inputProps={{ "aria-label": "controlled" }}
            />
        )
    }

    const title = "enter LMS Mode";
    const body = "automatically download a copy of your current config to the device accessing this dialog, and set your AmpliPro to a locked-down mode for use with third party frontend software.";
    const success = "LMS Mode activated successfully!";
    return(
        <ConfigPanel Base={Base} handler={LMSModeHandler} Contents={Contents} modalTitle={title} modalBody={body} successText={success} />
    )
}
