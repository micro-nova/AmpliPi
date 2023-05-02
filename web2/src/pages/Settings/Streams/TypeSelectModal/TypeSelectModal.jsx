import "./TypeSelectModal.scss"
import StreamTemplates from "../StreamTemplates.json"
import Modal from "@/components/Modal/Modal"
import Card from "@/components/Card/Card"
import { Divider } from "@mui/material"
import { getIcon } from "@/App.jsx"

const TypeSelectModal = ({ onClose, onSelect }) => {
  return (
    <>
      <Modal className="streams-modal" onClose={onClose}>
        <Card className="type-select-card">
          <div className="type-select-title">Select A Stream Type</div>
          <div>
            {StreamTemplates.filter(t=>!t.noCreate).map((t) => {
              return (
                <>
                <div
                  className="type-select-item"
                  key={t.type}
                  onClick={() => {
                    onSelect(t.type)
                    onClose()
                  }}
                >
                  <img className="type-icon" src={getIcon(t.type)}/>
                  {t.name}
                </div>
                <Divider/>
                </>
              )
            })}
          </div>
        </Card>
      </Modal>
    </>
  )
}

export default TypeSelectModal
