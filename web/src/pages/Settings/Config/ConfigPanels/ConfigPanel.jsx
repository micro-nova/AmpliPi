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
        Base,
        Contents,
        handler,
        modalTitle,
        modalBody,
        successText,
    } = props;

    const [loading, setLoading] = React.useState(false);
    const [modalOpen, setModalOpen] = React.useState(false);
    const [statusOpen, setStatusOpen] = React.useState(false);
    const [success, setSuccess] = React.useState(false);
    const statusBody = React.useRef("");

    function handleLoad() {
        setLoading(true);
        setModalOpen(false);

        const response = handler();
        if(response.ok){
            setLoading(false);
            setSuccess(true);
            statusBody.current = successText;
            setStatusOpen(true);
        } else {
            response.json().then(
                (data) => {
                    setLoading(false);
                    setSuccess(false);
                    statusBody.current = data.detail.message;
                    setStatusOpen(true);
                }
            );
        }
    };


    function StatusBar() {
        function PassFail() {
            if(success){
                return("success");
            } else {
                return("error");
            }
        }

        return(
            <Snackbar
                autoHideDuration={6000}
                anchorOrigin={{vertical: "bottom", horizontal: "left"}}
                open={statusOpen}
                onClose={() => {setStatusOpen(false)}}
            >
                <Alert onClose={() => {setStatusOpen(false);}} severity={() => {return PassFail();}} variant="filled" sx={{width: "100%"}}>
                    {statusBody.current}
                </Alert>
            </Snackbar>
        )
    }

    if(loading){
        return(
            <>
                <Base>
                    <CircularProgress />
                </Base>
                <Divider />
            </>
        )
    } else {
        function useFunction() {
            // Not all buttons need an 'Are you sure?' before executing their function
            // This function modulates whether clicking the button does the thing directly, or if it has a layer of indirection to the modal
            if(modalTitle && modalBody){
                setModalOpen(true);
            } else {
                return handleLoad();
            }
        }
        return(
            <>
                <Base>
                    <Contents useFunction={() => {useFunction();}}/>
                </Base>
                <StatusBar />
                <Divider />

                <Dialog open={modalOpen} maxWidth="xs">
                    <DialogTitle>
                        Are you sure you wish to {modalTitle}?
                    </DialogTitle>
                    <DialogContent>
                        This will {modalBody}
                    </DialogContent>
                    <Button variant="contained" color="error" fullWidth onClick={() => {setModalOpen(false);}}>No</Button>
                    <Button variant="contained" color="success" fullWidth onClick={() => {handleLoad();}}>Yes</Button>
                </Dialog>

            </>
        )
    }
}
