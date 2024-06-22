import React from "react";
import Divider from "@mui/material/Divider/Divider";
import CircularProgress from "@mui/material/CircularProgress/CircularProgress";

export default function ConfigPanel(props) {
    const {
        title,
        subheader,
        children,
        loading,
    } = props;

    return(
        <>
            <div>
                {title}
                <div className="config-desc">
                    {subheader}
                </div>
                    {loading && <CircularProgress />}
                    {!loading && children}
            </div>
            <Divider />
        </>
    )
}
