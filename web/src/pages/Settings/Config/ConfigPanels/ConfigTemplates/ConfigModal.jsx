import React from "react";
import Dialog from "@mui/material/Dialog/Dialog";
import DialogTitle from "@mui/material/DialogTitle/DialogTitle";
import DialogContent from "@mui/material/DialogContent/DialogContent";
import Button from "@mui/material/Button/Button";

export default function ConfigModal(props) {
    const {
        body,
        confirm,
        open,
        setOpen,
    } = props;

    return(
        <Dialog open={open} maxWidth="xs">
            <DialogTitle style={{textAlign: "center"}}>
                Are you sure?
            </DialogTitle>
            <DialogContent>
                {body}
            </DialogContent>
            <Button variant="contained" color="error" fullWidth onClick={() => {setOpen(false);}}>No</Button>
            <Button variant="contained" color="success" fullWidth onClick={() => {confirm();}}>Yes</Button>
        </Dialog>
    )
}
