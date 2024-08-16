import React from "react";
import PropTypes from "prop-types";
import "./StatusBars.scss";

import Alert from "@mui/material/Alert";

export default function AlertBar(props) {
    const {
        open,
        status,
        text,
        onClose,
        renderAnimationState,
    } = props;

    const alertRef = React.useRef(null);

    React.useEffect(() => {
        if(alertRef.current != null){
            const alertComp = alertRef.current;
            alertComp.classList.remove("error");
            if(status == false){
                alertComp.offsetWidth;
                alertComp.classList.add("error");
            }
        }
    }, [status, renderAnimationState]);

    if(open){
        return(
            <Alert
                ref={alertRef}
                onClose={onClose}
                severity={status ? "success" : "error"}
                variant="filled"
                style={{width: "100%",}}
            >
                {text}
            </Alert>
        )
    }
};
AlertBar.propTypes = {
    open: PropTypes.bool.isRequired,
    status: PropTypes.bool.isRequired,
    text: PropTypes.string.isRequired,
    onClose: PropTypes.func.isRequired,
    renderAnimationState: PropTypes.int,
};
AlertBar.defaultProps = {
    renderAnimationState: 1,
}
