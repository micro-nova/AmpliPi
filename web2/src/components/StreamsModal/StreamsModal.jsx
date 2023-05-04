import "./StreamsModal.scss"
import ModalCard from "@/components/ModalCard/ModalCard"
import { useStatusStore } from "@/App"
import { Divider } from "@mui/material"
import { getIcon } from "@/utils/getIcon"
import { getSourceInputType } from "@/utils/getSourceInputType"

//TODO: fix RCA behavior

let applyAction = null

export const executeApplyAction = () => {
  if (applyAction !== null) applyAction()
  applyAction = null
}

const StreamsModal = ({ sourceId, onApply=(_)=>{}, onClose=()=>{}, showClosePlayer=false, applyImmediately=true }) => {
  const streams = useStatusStore(state => state.status.streams)
  const zones = useStatusStore(state => state.status.zones)
  const sources = useStatusStore(state => state.status.sources)

  const setStream = (stream) => {
    const streamId = stream.id

    let currentSourceId = sourceId
    // RCA can only be used on its associated source, so swap if necessary
    const moveSource = stream.type === 'rca' && stream.index != sourceId
    if (moveSource) {
      // TODO: this should be a new endpoint. could benefit from combining the stream/zone transfer into one operation.
      currentSourceId = stream.index
      // move whatever is here to the original source

    }

    const apply = () => {
      if (moveSource) {
        const from = sourceId
        const to = currentSourceId
        const zoneIds = zones.filter(z => z.source_id === from).map(z => z.id)
        const fromStreamInput = sources[from].input

        // move zones
        fetch("/api/zones", {
          method: "PATCH",
          headers: {
            "Content-type": "application/json",
          },
          body: JSON.stringify({
            "zones": zoneIds,
            "update": {
              "source_id": to,
            }
          })
        })

        // move stream
        const streamType = getSourceInputType(sources[from])
        // only move digital streams; rca, none, unknown don't need to be moved
        if (streamType === "digital") {
          fetch(`/api/sources/${to}`, {
            method: "PATCH",
            headers: {
              "Content-type": "application/json",
            },
            body: JSON.stringify({
              "input": fromStreamInput
            })
          })
        }
      }

      fetch(`/api/sources/${currentSourceId}`, {
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

    return currentSourceId
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

    return sourceId
  }

  let streamsList = []

  for (const stream of streams) {
    const icon = getIcon(stream.type)
    streamsList.push(
      <>
        <div
          className="streams-modal-list-item"
          onClick={() => {
            onApply(setStream(stream))
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

  if (showClosePlayer) {
    streamsList.push(
        <div
          className="streams-modal-list-item"
          onClick={() => {
            onApply(removeStream())
            onClose()
          }}
          key={-1}
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
