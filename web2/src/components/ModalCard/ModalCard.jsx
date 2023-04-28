import Modal from '@/components/Modal/Modal'
import Card from '@/components/Card/Card'
import './ModalCard.scss'

const ModalCard = ({ header, children, onClose }) => {
  return (
    <Modal className="modal" onClose={onClose}>
      <Card className="modal-card">
        <div className="modal-header">{header}</div>
        <div className="modal-body">{children}</div>
      </Card>
    </Modal>
  )
}

export default ModalCard