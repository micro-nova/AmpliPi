import React from "react";
import PropTypes from "prop-types";
import "../PageBody.scss";
import "./Config.scss";

import PageHeader from "@/components/PageHeader/PageHeader";

import UploadConfig from "./ConfigPanels/UploadConfig.jsx";
import DownloadConfig from "./ConfigPanels/DownloadConfig.jsx";
import FactoryConfig from "./ConfigPanels/FactoryConfig.jsx";
import LMSMode from "./ConfigPanels/LMSMode.jsx";
import HardwareReset from "./ConfigPanels/HardwareReset.jsx";
import HardwareReboot from "./ConfigPanels/HardwareReboot.jsx";
import HardwareShutdown from "./ConfigPanels/HardwareShutdown.jsx";

export default function Config(props) {
    const { onClose } = props;
    return (
        <div className="page-container">
            <PageHeader title="Config" onClose={onClose} />
            <div className="page-body">
                <UploadConfig />

                <DownloadConfig />

                <FactoryConfig />

                <LMSMode />

                <HardwareReset />

                <HardwareReboot />

                <HardwareShutdown />
            </div>
        </div>
    );
};
Config.propTypes = {
    onClose: PropTypes.func.isRequired,
};
