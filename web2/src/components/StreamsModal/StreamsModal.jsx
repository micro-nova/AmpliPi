import "./StreamsModal.scss";
import Modal from "../Modal/Modal";
import Card from "../Card/Card";
import StreamBadge from "../StreamBadge/StreamBadge";
import { useStatusStore } from "@/App";

const StreamsModal = ({ sourceId, setStreamModalOpen, onClose }) => {

  const streams = useStatusStore((state) => state.status.streams)

  const setStream = (streamId) => {
    setStreamModalOpen(false)

    fetch(`/api/sources/${sourceId}`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({ input: `stream=${streamId}` }),
    });
  }

  const removeStream = () => {
    setStreamModalOpen(false)

    fetch(`/api/sources/${sourceId}`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({ input: "None" }),
    });
  }

  let streamsList = []

  for (const stream of streams) {
    streamsList.push(
      <div className="streams-modal-list-item" onClick={()=>{setStream(stream.id)}} key={stream.id}>
        {`${stream.name} - ${stream.type}`}
      </div>
    )
  }

  streamsList.push(
    <div className="streams-modal-list-item" onClick={()=>{removeStream()}} key="none">Close Player</div>
  )
  streamsList.push(
    <div className="streams-modal-list-item" onClick={()=>{setStreamModalOpen(false)}} key="cancel">Cancel</div>
  )


  return(
    <Modal className="streams-modal" onClose={onClose}>
      <Card className="streams-modal-card">
        <div className="streams-modal-header">
          Select Stream
        </div>
        <div className="streams-modal-body">
          {streamsList}
        </div>
      </Card>
    </Modal>
  )
}

export default StreamsModal
