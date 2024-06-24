import React from "react";
import Dialog from "@mui/material/Dialog/Dialog";
import DialogTitle from "@mui/material/DialogTitle/DialogTitle";
import DialogContent from "@mui/material/DialogContent/DialogContent";
import Button from "@mui/material/Button/Button";
import PropTypes from "prop-types";

export default function ConfigModal(props) {
    const {
        body,
        onApply,
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
            <Button variant="contained" color="success" fullWidth onClick={() => {onApply(); setOpen(false);}}>Yes</Button>
        </Dialog>
    )
}
ConfigModal.propTypes = {
    body: PropTypes.string.isRequired,
    onApply: PropTypes.func.isRequired,
    open: PropTypes.bool.isRequired,
    setOpen: PropTypes.func.isRequired,
};
