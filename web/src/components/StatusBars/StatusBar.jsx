import React from "react";
import PropTypes from "prop-types";
import "./StatusBars.scss";
import Snackbar from "@mui/material/Snackbar";

import Alert from "@mui/material/Alert";

export default function StatusBar(props) {
    const {
        open,
        success,
        text,
        onClose,
        anchorOrigin,
        autoHideDuration,
    } = props;

    const [closedText, setClosedText] = React.useState(""); // If a user has closed a given message, don't show it again until another message tries to appear

    return(
        <Snackbar
            className="snackbar"
            autoHideDuration={autoHideDuration != 0 ? autoHideDuration : 999999999999999}
            anchorOrigin={anchorOrigin}
            open={open && closedText != text}
            onClose={() => {onClose(); setClosedText(text);}}
        >
            <Alert // Cannot be AlertBar due to React rendering throwing errors despite it being the same thing
                onClose={() => {onClose(); setClosedText(text);}}
                severity={success ? "success" : "error"}
                variant="filled"
                style={{width: "100%"}}
            >
                {text}
            </Alert>
        </Snackbar>
    );
}
StatusBar.propTypes = {
    open: PropTypes.bool.isRequired,
    success: PropTypes.bool,
    text: PropTypes.string.isRequired,
    onClose: PropTypes.func.isRequired,
    autoHideDuration: PropTypes.number,
    anchorOrigin: PropTypes.object,
};
StatusBar.defaultProps = {
    success: false,
    autoHideDuration: 3000,
    anchorOrigin: {vertical: "bottom", horizontal: "left"},
};

