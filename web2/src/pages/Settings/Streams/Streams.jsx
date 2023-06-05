import PageHeader from "@/components/PageHeader/PageHeader"
import "./Streams.scss"
import "../PageBody.scss"
import { useStatusStore } from "@/App.jsx"
import { useState } from "react"
import StreamModal from "./StreamModal/StreamModal"
import Fab from "@mui/material/Fab"
import AddIcon from "@mui/icons-material/Add"
import TypeSelectModal from "./TypeSelectModal/TypeSelectModal"
import StreamTemplates from "./StreamTemplates.json"
import { getIcon } from "@/utils/getIcon"
import List from "@/components/List/List"
import ListItem from "@/components/List/ListItem/ListItem"

const initEmptyStream = (type) => {
  const streamTemplate = StreamTemplates.filter((t) => t.type === type)[0]
  let stream = { type: type, disabled: false }
  streamTemplate.fields.forEach((field) => {
    stream[field.name] = field.default
  })
  return stream
}

const applyStreamChanges = (stream) => {
  fetch(`/api/streams/${stream.id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(stream),
  })
}

const makeNewStream = (stream) => {
  fetch(`/api/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(stream),
  })
}

const deleteStream = (stream) => {
  fetch(`/api/streams/${stream.id}`, { method: "DELETE" })
}

const StreamListItem = ({ stream }) => {
  const [showModal, setShowModal] = useState(false)
  const icon = getIcon(stream.type)
  return (
    <ListItem
      key={stream.id}
      name={stream.name}
      onClick={() => setShowModal(true)}
    >
      <img src={icon} className="stream-modal-icon" alt="stream icon" />

      {showModal && (
        <StreamModal
          stream={stream}
          onClose={() => {
            setShowModal(false)
          }}
          apply={applyStreamChanges}
          del={deleteStream}
        />
      )}
    </ListItem>
  )
}

const Streams = ({ onClose }) => {
  const streams = useStatusStore((state) => state.status.streams)
  const [showModal, setShowModal] = useState(false)
  const [showSelect, setShowSelect] = useState(false)
  const [selectedType, setSelectedType] = useState("")

  return (
    <div className="page-container">
      <PageHeader title="Streams" onClose={onClose} />
      <div className="page-body">
        <List>
          {streams.map((stream) => {
            return <StreamListItem key={stream.id} stream={stream} />
          })}
        </List>
        <div className="add-button">
          <Fab onClick={() => setShowSelect(true)}>
            <AddIcon />
          </Fab>
        </div>
      </div>

      {showSelect && (
        <TypeSelectModal
          onClose={() => {
            setShowSelect(false)
          }}
          onSelect={(type) => {
            setSelectedType(type)
            setShowSelect(false)
            setShowModal(true)
          }}
        />
      )}
      {showModal && (
        <StreamModal
          stream={initEmptyStream(selectedType)}
          apply={makeNewStream}
          onClose={() => {
            setShowModal(false)
          }}
        />
      )}
    </div>
  )
}

export default Streams
