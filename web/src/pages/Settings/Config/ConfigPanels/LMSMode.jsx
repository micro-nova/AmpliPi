import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import { useStatusStore } from "@/App.jsx";
import Switch from '@mui/material/Switch/Switch';
import { IsMobileApp } from "@/utils/MobileApp";

export default function LMSMode() {
    const lmsMode = useStatusStore((s) => s.status.info.lms_mode);

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

    const LMSModeHandler = () => {
        DownloadConfig();
        const response = fetch("/api/lms_mode", { method: "POST" });
        return response;
    };

    function Contents(props) {
        const { useFunction } = props;
        return(
            <Switch
                checked={lmsMode}
                onChange={useFunction}
                inputProps={{ "aria-label": "controlled" }}
            />
        )
    }


    if(!lmsMode){ // Bimodal due to different text whether activating or deactivating LMs mode
        return(
            <ConfigPanel
                title={"Lyrion Media Server (LMS) Mode"}
                subheader={"Toggles LMS Mode on or off. LMS is useful for piggy-backing off integrations AmpliPi does not have natively. This will wipe out the current config! As a result, it downloads the current config before proceeding with LMS mode."}
                handler={LMSModeHandler}
                Contents={Contents}
                modalBody={"This will automatically download a copy of your current config to the device accessing this dialog, and set your AmpliPro to a locked-down mode for use with third party frontend software."}
                successText={"LMS Mode activated successfully!"}
            />
        )
    } else {
        return(
            <ConfigPanel
                title={"Lyrion Media Server (LMS) Mode"}
                subheader={"Toggles LMS Mode on or off. LMS is useful for piggy-backing off integrations AmpliPi does not have natively. This will wipe out the current config! As a result, it downloads the current config before proceeding with LMS mode."}
                handler={LMSModeHandler}
                Contents={Contents}
                modalBody={"This will reset AmpliPi to factory settings, you will have to either manually reconfigure it or reupload the config that was downloaded when LMS mode was initially toggled."}
                successText={"LMS Mode deactivated successfully!"}
            />
        )
    }
}
