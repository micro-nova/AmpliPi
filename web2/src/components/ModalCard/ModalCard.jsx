import Modal from '@/components/Modal/Modal'
import Card from '@/components/Card/Card'
import './ModalCard.scss'
import { IconButton } from '@mui/material'
import CheckIcon from '@mui/icons-material/Check';
import DeleteIcon from '@mui/icons-material/Delete';
import CloseIcon from '@mui/icons-material/Close';

const ModalCard = ({ header, children, footer, onClose, onAccept=null, onCancel=null, onDelete=null}) => {
  return (
    <Modal className="modal" onClose={onClose}>
      <Card className="modal-card">
        <div className="modal-header">{header}</div>
        <div className="modal-body">{children}</div>
        <div className="modal-footer">
          {footer}
          {onAccept && <CheckIcon className="modal-footer-button" onClick={onAccept} fontSize='inherit'/>}
          {onCancel && <CloseIcon className="modal-footer-button" onClick={onCancel} fontSize='inherit'/>}
          {onDelete && <DeleteIcon className="modal-footer-button" onClick={onDelete} fontSize='inherit'/>}
        </div>
      </Card>
    </Modal>
  )
}

export default ModalCard
