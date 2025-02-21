import React from "react";
import Modal from "@/components/Modal/Modal";
import Card from "@/components/Card/Card";
import "./ModalCard.scss";
import CustomMarquee from "../CustomMarquee/CustomMarquee";
import Grid from "@mui/material/Grid/Grid";
import Button from "@mui/material/Button/Button";

import PropTypes from "prop-types";

const ModalCard = ({
    header,
    children,
    footer,
    onClose,
    buttons,
}) => {
    React.useEffect(() => {
        const handleKeyDown = (event) => {
            if(event.key === "Escape") {
                onClose();
            }
        };

        window.addEventListener('keydown', handleKeyDown);

        return () => {window.removeEventListener('keydown', handleKeyDown);}
    }, [])

    const footerContent = buttons.map(([text, onClick], index) => {
        return(
            <Grid item key={index}>
                <Button onClick={onClick}>{text}</Button>
            </Grid>
        )
    })

    const headerRef = React.useRef(null);
    return (
        <Modal className="modal" onClose={onClose}>
            <Card className="modal-card">
                <div className="modal-header" ref={headerRef}>
                    <CustomMarquee children={header} containerRef={headerRef}/>
                </div>
                <div className="modal-body pill-scrollbar">{children}</div>
                <div className="modal-footer">
                    {footer}
                </div>
                <Grid
                    container
                    spacing={"auto"}
                    columns={buttons.length}
                    direction={"row"}
                    sx={{
                        padding: "5px",
                        justifyContent: "space-around",
                    }}
                >
                    {footerContent}
                </Grid>
            </Card>
        </Modal>
    );
};
ModalCard.propTypes = {
    header: PropTypes.string,
    children: PropTypes.any.isRequired,
    footer: PropTypes.any,
    onClose: PropTypes.func.isRequired,
    buttons: PropTypes.array
};
ModalCard.defaultProps={
    buttons: [],
};

export default ModalCard;
