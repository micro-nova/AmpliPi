
import React from 'react';
import "../Config.scss";
import ConfigPanel from './ConfigPanel.jsx';
import Button from '@mui/material/Button/Button';

export default function FactoryConfig(){
    const FactoryReset = () => {
        const response = fetch("/api/factory_reset", { method: "POST" });
        return response;
    };

    function Contents(props) {
        const { onClick } = props;
        return(
            <Button onClick={onClick}>Reset</Button>
        )
    }

    return(
        <ConfigPanel
            title={"Factory Config"}
            subheader={"Resets Amplipi to the factory default configuration. We recommend downloading the current configuration beforehand."}
            handler={FactoryReset}
            Contents={Contents}
            modalBody={"This will reset all settings to factory default, ensure you've downloaded your current config if you wish to keep it!"}
            successText={"AmpliPi reset to factory settings successfully!"}
        />
    )
}
