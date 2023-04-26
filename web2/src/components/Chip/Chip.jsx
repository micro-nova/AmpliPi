import './Chip.scss'

const Chip = ({ children, onClick }) => {
  return (
    <div className="chip" onClick={onClick}>
      {children}
    </div>
  )
}

export default Chip