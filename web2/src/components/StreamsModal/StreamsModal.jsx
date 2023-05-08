import "./StreamsModal.scss"
import ModalCard from "@/components/ModalCard/ModalCard"
import { getIcon, useStatusStore } from "@/App"
import List from "@/components/List/List"
import ListItem from "../List/ListItem/ListItem"

//TODO: fix RCA behavior

const LIST_ITEM_FONT_SIZE = "1.5rem"

let applyAction = null

export const executeApplyAction = () => {
  if (applyAction !== null) applyAction()
  applyAction = null
}

const StreamsModal = ({ sourceId, onApply=()=>{}, onClose=()=>{}, applyImmediately=true }) => {
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
      <ListItem
        name={stream.name}
        key={stream.id}
        onClick={() => {
          setStream(stream.id)
          onApply()
          onClose()
        }
      }
      nameFontSize = {LIST_ITEM_FONT_SIZE}
      >
        <img src={icon} className="streams-modal-icon" alt="stream icon" />
      </ListItem>
    )
  }

  streamsList.push(
    <ListItem name="Cancel" onClick={onClose} key="cancel" nameFontSize = {LIST_ITEM_FONT_SIZE}/>
  )

  return (
    <ModalCard header="Select Stream" onClose={onClose}>
      <List>
      {streamsList}
      </List>
    </ModalCard>
  )
}

export default StreamsModal
