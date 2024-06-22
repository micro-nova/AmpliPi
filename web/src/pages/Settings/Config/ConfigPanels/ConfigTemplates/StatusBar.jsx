import React from "react";
import { Snackbar, Alert } from "@mui/material";


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
            if(response.ok){
                setSuccess(true);
                text.current = successText;
            } else {
                const data = await response.json();
                setSuccess(false);
                text.current = data.detail.message;
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
                {successText}
            </Alert>
        </Snackbar>
    );
}
