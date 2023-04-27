import "./Modal.scss"
import StopProp from "@/components/StopProp/StopProp"

const Modal = ({ children, className = "", onClose }) => {
  return (
    <div
      className={`modal_container ${className}`}
      onClick={(e) => {
        onClose()
        e.stopPropagation()
      }}
    >
      <StopProp>
        {children}
      </StopProp>
    </div>
  )
}

export default Modal
