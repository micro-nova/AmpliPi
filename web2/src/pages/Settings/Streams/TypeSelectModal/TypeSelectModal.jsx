import "./TypeSelectModal.scss"
import StreamTemplates from "../StreamTemplates.json"
import Modal from "@/components/Modal/Modal"
import Card from "@/components/Card/Card"

const TypeSelectModal = ({ onClose, onSelect }) => {
  return (
    <>
      <Modal className="streams-modal" onClose={onClose}>
        <Card className="type-select-card">
          <div className="type-select-title">Select A Stream Type</div>
          <div>
            {StreamTemplates.map((t) => {
              return (
                <div
                  key={t.type}
                  onClick={() => {
                    onSelect(t.type)
                    onClose()
                  }}
                >
                  {t.name}
                </div>
              )
            })}
          </div>
        </Card>
      </Modal>
    </>
  )
}

export default TypeSelectModal
