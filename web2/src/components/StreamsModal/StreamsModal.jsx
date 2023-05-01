import "./StreamsModal.scss"
import ModalCard from "@/components/ModalCard/ModalCard"
import { getIcon, useStatusStore } from "@/App"

//TODO: fix RCA behavior

let applyAction = null

export const executeApplyAction = () => {
  if (applyAction !== null) applyAction()
  applyAction = null
}

const StreamsModal = ({ sourceId, onApply=()=>{}, onClose=()=>{}, showClosePlayer=false, applyImmediately=true }) => {
  const streams = useStatusStore((state) => state.status.streams)

  const setStream = (streamId) => {
    const apply = () => {
      fetch(`/api/sources/${sourceId}`, {
        method: "PATCH",
        headers: {
          "Content-type": "application/json",
        },
        body: JSON.stringify({ input: `stream=${streamId}` }),
      })
    }

    if (applyImmediately) {
      apply()
    } else {
      applyAction = apply
    }
  }

  const removeStream = () => {
    const apply = () => {
      fetch(`/api/sources/${sourceId}`, {
        method: "PATCH",
        headers: {
          "Content-type": "application/json",
        },
        body: JSON.stringify({ input: "None" }),
      })
    }

    if (applyImmediately) {
      apply()
    } else {
      applyAction = apply
    }

  }

  let streamsList = []

  for (const stream of streams) {
    const icon = getIcon(stream.type)
    streamsList.push(
      <div
        className="streams-modal-list-item"
        onClick={() => {
          setStream(stream.id)
          onApply()
          onClose()
        }}
        key={stream.id}
      >
        <img src={icon} className="streams-modal-icon" alt="stream icon" />
        {stream.name}
      </div>
    )
  }

  if (showClosePlayer) {
    streamsList.push(
      <div
        className="streams-modal-list-item"
        onClick={() => {
          removeStream()
          onApply()
          onClose()
        }}
        key="none"
      >
        Close Player
      </div>
    )
  }

  streamsList.push(
    <div
      className="streams-modal-list-item"
      onClick={() => {
        // setStreamModalOpen(false)
        onClose()
      }}
      key="cancel"
    >
      Cancel
    </div>
  )

  return (
    <ModalCard header="Select Stream" onClose={onClose}>
      {streamsList}
    </ModalCard>
  )
}

export default StreamsModal
