import "./StreamsModal.scss"
import ModalCard from "@/components/ModalCard/ModalCard"
import { getIcon, useStatusStore } from "@/App"

//TODO: fix RCA behavior

const StreamsModal = ({ sourceId, setStreamModalOpen, onClose, showClosePlayer=false }) => {
  const streams = useStatusStore((state) => state.status.streams)

  const setStream = (streamId) => {
    setStreamModalOpen(false)

    fetch(`/api/sources/${sourceId}`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({ input: `stream=${streamId}` }),
    })
  }

  const removeStream = () => {
    setStreamModalOpen(false)

    fetch(`/api/sources/${sourceId}`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({ input: "None" }),
    })
  }

  let streamsList = []

  for (const stream of streams) {
    const icon = getIcon(stream.type)
    streamsList.push(
      <div
        className="streams-modal-list-item"
        onClick={() => {
          setStream(stream.id)
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
