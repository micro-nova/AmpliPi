import "./StreamsModal.scss"
import ModalCard from "@/components/ModalCard/ModalCard"
import { useStatusStore } from "@/App"
import { Divider } from "@mui/material"
import { getIcon } from "@/utils/getIcon"
import { getSourceInputType } from "@/utils/getSourceInputType"
import { setRcaSourceId } from "../ZonesModal/ZonesModal"
import { moveSourceContents, setSourceStream } from "@/utils/APIHelper"
import { setRcaStatus } from "../ZonesModal/ZonesModal"

//TODO: fix RCA behavior

let applyAction = null
let statusModified = null

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
      console.log(`will move ${currentSourceId} to ${sourceId}`)
    }

    const apply = () => {
      if (moveSource) {
        // move then set new stream
        // moveZonesStreamLocal(currentSourceId, sourceId)
        statusModified = JSON.parse(JSON.stringify(status))
        return moveSourceContents(status, currentSourceId, sourceId).then(() => {
          statusModified.zones.forEach(z => {
            if (z.source_id === currentSourceId) {
              console.log(`moving zone ${z.id} from ${z.source_id} to ${sourceId}`)
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
      <>
        <div
          className="streams-modal-list-item"
          onClick={() => {
            onApply()
            setStream(stream)
            onClose()
          }}
          key={stream.id}
        >
          <img src={icon} className="streams-modal-icon" alt="stream icon" />
          {stream.name}
        </div>

        <Divider/>
      </>
    )
  }

  streamsList.push(
    <div
      className="streams-modal-list-item"
      onClick={() => {
        // setStreamModalOpen(false)
        onClose()
      }}
      key={-2}
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
