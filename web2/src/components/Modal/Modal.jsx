import "./Modal.scss"

const Modal = ({ children, className = "", onClose }) => {
  return (
    <div
      className={`modal_container ${className}`}
      onClick={onClose}
    >
      <div
        onClick={(e) => {
          e.stopPropagation()
        }}
      >
        {children}
      </div>
    </div>
  )
}

export default Modal
