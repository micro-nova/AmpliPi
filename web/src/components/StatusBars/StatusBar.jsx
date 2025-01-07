import React from "react";
import PropTypes from "prop-types";
import "./StatusBars.scss";
import Snackbar from "@mui/material/Snackbar";

import Alert from "@mui/material/Alert"

export default function StatusBar(props) {
    const {
        open,
        status,
        text,
        onClose,
    } = props;

    return(
        <Snackbar
            className="snackbar"
            autoHideDuration={3000}
            anchorOrigin={{vertical: "bottom", horizontal: "left"}}
            open={open}
            onClose={onClose}
        >
            <Alert // Cannot be AlertBar due to React rendering throwing errors despite it being the same thing
                onClose={onClose}
                severity={status ? "success" : "error"}
                variant="filled"
                style={{width: "100%"}}
            >
                {text}
            </Alert>
        </Snackbar>
    )
};
StatusBar.propTypes = {
    open: PropTypes.bool.isRequired,
    status: PropTypes.bool.isRequired,
    text: PropTypes.string.isRequired,
    onClose: PropTypes.func.isRequired,
};
