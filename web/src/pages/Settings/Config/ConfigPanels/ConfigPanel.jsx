import React from "react";
import Divider from "@mui/material/Divider/Divider";
import CircularProgress from "@mui/material/CircularProgress/CircularProgress";
import Dialog from "@mui/material/Dialog/Dialog";
import DialogTitle from "@mui/material/DialogTitle/DialogTitle";
import DialogContent from "@mui/material/DialogContent/DialogContent";
import Button from "@mui/material/Button/Button";
import Snackbar from "@mui/material/Snackbar/Snackbar";
import Alert from"@mui/material/Alert/Alert";

export default function ConfigPanel(props) {
    const {
        title,
        subheader,
        Contents, // Component that takes some sort of input (typically a button) and a "useFunction" prop (generally equivalent to onClick, termed "useFunction" due to switches using "onChange" instead)
        handler, // Required, the onClick/onChange function, taken separately from Contents' useFunction prop so we can control whether it's an onClick event or if it belongs to the "yes" button on the confirmation modal
        modalBody, // Optional, the content of the modal. Explains what you're doing when you hit "yes"
        successText, // Required, what the success popup says when there isn't any errors
    } = props;

    const [loading, setLoading] = React.useState(false);
    const [modalOpen, setModalOpen] = React.useState(false);
    const [statusOpen, setStatusOpen] = React.useState(false);
    const [success, setSuccess] = React.useState(false);
    const statusBody = React.useRef("");

    async function handleLoad() {
        setLoading(true);
        setModalOpen(false);

        const response = await handler(); // requires async-await or response.ok is undefined by the time the if statement is executed
        if(response.ok){
            setLoading(false);
            setSuccess(true);
            statusBody.current = successText;
        } else {
            const data = await response.json();
            setLoading(false);
            setSuccess(false);
            statusBody.current = data.detail.message;
        }
        setStatusOpen(true);
    };


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
            <div>
                {title}
                <div className="config-desc">
                    {subheader}
                </div>
                <CircularProgress />
            </div>
        )
    } else {
        function onClick() {
            // Not all buttons need an 'Are you sure?' before executing their function
            // This function modulates whether clicking the button does the thing directly, or if it has a layer of indirection to the modal
            if(modalBody){
                setModalOpen(true);
            } else {
                return handleLoad();
            }
        }
        return(
            <>
                <div>
                    {title}
                    <div className="config-desc">
                        {subheader}
                    </div>
                    <Contents onClick={() => {onClick();}}/>
                </div>
                <StatusBar />
                <Divider />

                <Dialog open={modalOpen} maxWidth="xs">
                    <DialogTitle style={{textAlign: "center"}}>
                        Are you sure?
                    </DialogTitle>
                    <DialogContent>
                        {modalBody}
                    </DialogContent>
                    <Button variant="contained" color="error" fullWidth onClick={() => {setModalOpen(false);}}>No</Button>
                    <Button variant="contained" color="success" fullWidth onClick={() => {handleLoad();}}>Yes</Button>
                </Dialog>

            </>
        )
    }
}
