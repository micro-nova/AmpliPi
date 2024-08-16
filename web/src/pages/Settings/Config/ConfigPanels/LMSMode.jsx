import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigTemplates/ConfigPanel.jsx';
import { useStatusStore } from "@/App.jsx";
import Switch from '@mui/material/Switch/Switch';
import ConfigDownload from './ConfigTemplates/ConfigDownload';
import ConfigModal from './ConfigTemplates/ConfigModal';
import ResponseBar from '@/components/StatusBars/ResponseBar.jsx';

export default function LMSMode() {
    const lmsMode = useStatusStore((s) => s.status.info.lms_mode);
    const [modalOpen, setModalOpen] = React.useState(false);
    const [loading, setLoading] = React.useState(false);
    const [response, setResponse] = React.useState(null);

    async function LMSModeHandler(){
        setLoading(true);
        const resp = await fetch("/api/lms_mode", { method: "POST" });
        setResponse(resp);
        setLoading(false);
    };

    function LMSModal(){
        if(lmsMode){
            return(
                <ConfigModal
                    body={"This will reset AmpliPi to factory settings, you will have to either manually reconfigure it or reupload the config that was downloaded when LMS mode was initially toggled."}
                    onApply={() => {ConfigDownload(); LMSModeHandler();}}
                    open={modalOpen}
                    setOpen={setModalOpen}
                />
            )
        } else {
            return(
                <ConfigModal
                    body={"This will automatically download a copy of your current config to the device accessing this dialog, and set your AmpliPro to a locked-down mode for use with third party frontend software."}
                    onApply={() => {ConfigDownload(); LMSModeHandler();}}
                    open={modalOpen}
                    setOpen={setModalOpen}
                />
            )
        }
    }


    return(
        <>
            <ConfigPanel
                title={"Lyrion Media Server (LMS) Mode"}
                subheader={"Toggles LMS Mode on or off. LMS is useful for piggy-backing off integrations AmpliPi does not have natively. This will wipe out the current config! As a result, it downloads the current config before proceeding with LMS mode."}
                loading={loading}
            >
                <Switch
                    checked={lmsMode}
                    onClick={() => {setModalOpen(true);}}
                    inputProps={{ "aria-label": "controlled" }}
                />
            </ConfigPanel>

            <LMSModal />
            <ResponseBar
                successText={"LMS Mode toggled successfully!"}
                response={response}
            />
        </>
    )
}
