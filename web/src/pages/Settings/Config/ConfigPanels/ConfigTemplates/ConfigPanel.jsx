import React from "react";
import Divider from "@mui/material/Divider/Divider";
import CircularProgress from "@mui/material/CircularProgress/CircularProgress";
import Snackbar from "@mui/material/Snackbar/Snackbar";
import Alert from"@mui/material/Alert/Alert";

export default function ConfigPanel(props) {
    const {
        title,
        subheader,
        children,
        successText,
        loading,
    } = props;

    // const [loading, setLoading] = React.useState(false);
    const [statusOpen, setStatusOpen] = React.useState(false);
    const [success, setSuccess] = React.useState(false);
    const statusBody = React.useRef("");

    function StatusBar() {
        const severity = success ? "success" : "error";

        return(
            <Snackbar
                autoHideDuration={3000}
                anchorOrigin={{vertical: "bottom", horizontal: "left"}}
                open={statusOpen}
                onClose={() => {setStatusOpen(false)}}
            >
                <Alert
                    onClose={() => {setStatusOpen(false);}}
                    severity={severity}
                    variant="filled"
                    style={{width: "100%"}}
                >
                    {statusBody.current}
                </Alert>
            </Snackbar>
        )
    }

    if(loading){
        return(
            <>
                <div>
                    {title}
                    <div className="config-desc">
                        {subheader}
                    </div>
                    <CircularProgress />
                </div>
                <StatusBar />
                <Divider />
            </>
        )
    } else {
        return(
            <>
                <div>
                    {title}
                    <div className="config-desc">
                        {subheader}
                    </div>
                    {children}
                </div>
                <StatusBar />
                <Divider />
            </>
        )
    }
}
