import React from "react";
import PropTypes from "prop-types";
import "./StatusBars.scss";

import Alert from "@mui/material/Alert";

export default function AlertBar(props) {
    const {
        open,
        success,
        text,
        onClose,
        renderAnimationState,
    } = props;

    const alertRef = React.useRef(null);

    React.useEffect(() => {
        if(alertRef.current != null){
            const alertComp = alertRef.current;
            alertComp.classList.remove("error");
            if(!success){
                alertComp.offsetWidth;
                alertComp.classList.add("error");
            }
        }
    }, [success, renderAnimationState]);

    const [closedText, setClosedText] = React.useState(""); // If a user has closed a given message, don't show it again until another message tries to appear

    if(open && text != closedText){
        return(
            <Alert
                ref={alertRef}
                onClose={() => {onClose(); setClosedText(text);}}
                severity={success ? "success" : "error"}
                variant="filled"
                style={{width: "100%",}}
            >
                {text}
            </Alert>
        );
    }
}
AlertBar.propTypes = {
    open: PropTypes.bool.isRequired,
    success: PropTypes.bool,
    text: PropTypes.string.isRequired,
    onClose: PropTypes.func.isRequired,
    renderAnimationState: PropTypes.number,
};
AlertBar.defaultProps = {
    success: false,
    renderAnimationState: 1,
};
