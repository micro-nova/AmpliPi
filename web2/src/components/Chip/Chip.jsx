import './Chip.scss'
import StopProp from "@/components/StopProp/StopProp"

const Chip = ({ children, onClick }) => {
  return (
    <StopProp>
      <div className="chip" onClick={onClick}>
        {children}
      </div>
    </StopProp>
  )
}

export default Chip