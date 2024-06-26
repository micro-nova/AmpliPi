import React from "react";
import { Snackbar, Alert } from "@mui/material";
import PropTypes from "prop-types";


export default function StatusBar(props) {
    const {
        successText,
        response,
    } = props;

    const [open, setOpen] = React.useState(false);
    const [success, setSuccess] = React.useState(false);
    const text = React.useRef("");

    async function handleSuccess() {
        if(response != null){
            try {
                const res = await response;
                if (res.ok) {
                    setSuccess(true);
                    text.current = successText;
                } else {
                    const data = await res.json();
                    setSuccess(false);
                    text.current = data.detail.message;
                }
            } catch (error) {
                setSuccess(false);
                text.current = `An error occurred while FETCHing: ${error.message}`;
            }
            setOpen(true);
        }
    };

    React.useEffect(() => {
        handleSuccess();
    }, [response]);

    return(
        <Snackbar
            autoHideDuration={3000}
            anchorOrigin={{vertical: "bottom", horizontal: "left"}}
            open={open}
            onClose={() => {setOpen(false);}}
        >
            <Alert
                onClose={() => {setOpen(false);}}
                severity={success ? "success" : "error"}
                variant="filled"
                style={{width: "100%"}}
            >
                {text.current}
            </Alert>
        </Snackbar>
    );
}
StatusBar.propTypes = {
    successText: PropTypes.string.isRequired,
    response: PropTypes.instanceOf(Promise).isRequired,
};

