import React from "react";
import { CircularProgress } from "@mui/material";
import "./LoadingPage.scss";
import AmplipiLogo from "@/../static/imgs/amplipi_logo.png";

const LoadingPage = () => {
    return (
        <div className="loading-container">
            <img src={AmplipiLogo} className="loading-logo" />
            <CircularProgress />
        </div>
    );
};

export default LoadingPage;
