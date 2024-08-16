import React from "react";
import Modal from "@/components/Modal/Modal";
import Card from "@/components/Card/Card";
import "./ModalCard.scss";
import CheckIcon from "@mui/icons-material/Check";
import DeleteIcon from "@mui/icons-material/Delete";
import CloseIcon from "@mui/icons-material/Close";
import CustomMarquee from "../CustomMarquee/CustomMarquee";

import PropTypes from "prop-types";

const ModalCard = ({
    header,
    children,
    footer,
    onClose,
    onAccept = null,
    onCancel = null,
    onDelete = null,
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

    const headerRef = React.useRef(null);
    return (
        <Modal className="modal" onClose={onClose}>
            <Card className="modal-card">
                <div className="modal-header" ref={headerRef}>
                    <CustomMarquee children={header} containerRef={headerRef}/>
                </div>
                <div className="modal-body">{children}</div>
                <div className="modal-footer">
                    {footer}
                    {onAccept && (
                        <CheckIcon
                            className="modal-footer-button"
                            onClick={onAccept}
                            fontSize="inherit"
                        />
                    )}
                    {onCancel && (
                        <CloseIcon
                            className="modal-footer-button"
                            onClick={onCancel}
                            fontSize="inherit"
                        />
                    )}
                    {onDelete && (
                        <DeleteIcon
                            className="modal-footer-button"
                            onClick={onDelete}
                            fontSize="inherit"
                        />
                    )}
                </div>
            </Card>
        </Modal>
    );
};
ModalCard.propTypes = {
    header: PropTypes.string,
    children: PropTypes.any.isRequired,
    footer: PropTypes.string,
    onClose: PropTypes.func.isRequired,
    onAccept: PropTypes.func,
    onCancel: PropTypes.func,
    onDelete: PropTypes.func,
};
ModalCard.defaultProps={
    onAccept: null,
    onCancel: null,
    onDelete: null,
};

export default ModalCard;
