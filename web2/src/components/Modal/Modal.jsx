import './Modal.scss'

const Modal = ({children, className}) => {
    return (
        <div className={`modal_container ${className}`}>
            {children}
        </div>
    )
}

export default Modal
