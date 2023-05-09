import "./StreamsModal.scss"
import ModalCard from "@/components/ModalCard/ModalCard"
import { useStatusStore } from "@/App"
import { Divider } from "@mui/material"
import { getIcon } from "@/utils/getIcon"
import { getSourceInputType } from "@/utils/getSourceInputType"
import { setRcaSourceId } from "../ZonesModal/ZonesModal"
import { moveSourceContents, setSourceStream } from "@/utils/APIHelper"
import { setRcaStatus } from "../ZonesModal/ZonesModal"
import { getIcon, useStatusStore } from "@/App"
import List from "@/components/List/List"
import ListItem from "../List/ListItem/ListItem"


const LIST_ITEM_FONT_SIZE = "1.5rem"

let applyAction = null

export const executeApplyAction = () => {
  if (applyAction !== null) {
    const temp = applyAction
    applyAction = null
    return temp()
  }
}

const StreamsModal = ({ sourceId, onApply=()=>{}, onClose=()=>{}, showClosePlayer=false, applyImmediately=true }) => {
  const streams = useStatusStore(state => state.status.streams)
  const zones = useStatusStore(state => state.status.zones)
  const sources = useStatusStore(state => state.status.sources)
  const status = useStatusStore(state => state.status)

  const setStream = (stream) => {
    const streamId = stream.id

    let currentSourceId = sourceId
    // RCA can only be used on its associated source, so swap if necessary
    const moveSource = stream.type === 'rca' && stream.index != sourceId
    if (moveSource) {
      // TODO: this should be a new endpoint. could benefit from combining the stream/zone transfer into one operation.
      currentSourceId = stream.index
      // notify ZonesModal that we are using a different sourceId
      setRcaSourceId(currentSourceId)
      // move whatever is here to the original source
    }

    const apply = () => {
      if (moveSource) {
        // move then set new stream
        const statusModified = JSON.parse(JSON.stringify(status))
        return moveSourceContents(status, currentSourceId, sourceId).then(() => {
          statusModified.zones.forEach(z => {
            if (z.source_id === currentSourceId) {
              z.source_id = sourceId
            }
          })
          setRcaStatus(statusModified)
          setSourceStream(currentSourceId, streamId)
        })
      } else {
        // just set new stream
        return setSourceStream(currentSourceId, streamId)
      }
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
