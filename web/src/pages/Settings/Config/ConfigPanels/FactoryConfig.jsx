
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';

export default function FactoryConfig(){
    function Base(props) {
        const { children } = props;
        return(
            <div>
                Factory Config
                <div className="config-desc">
                    {
                        "Resets Amplipi to the factory default configuration. We recommend downloading the current configuration beforehand."
                    }
                </div>
                {children}
            </div>
        )
    }

    const FactoryReset = () => {
        const response = fetch("/api/factory_reset", { method: "POST" });
        return response;
    };

    function Contents(props) {
        const { useFunction } = props;
        return(
            <Button onClick={useFunction}>Reset</Button>
        )
    }

    const title = "reset to factory settings";
    const body = "Reset all settings to factory default, ensure you've downloaded your current config if you wish to keep it!";
    const success = "AmpliPi reset to factory settings successfully!";
    return(
        <ConfigPanel Base={Base} handler={FactoryReset} Contents={Contents} modalTitle={title} modalBody={body} successText={success} />
    )
}
