import React from "react";
import "./StreamsModal.scss"
import ModalCard from "@/components/ModalCard/ModalCard"
import { useStatusStore } from "@/App"
import { getIcon } from "@/utils/getIcon"
import { setRcaSourceId } from "../ZonesModal/ZonesModal"
import { moveSourceContents, setSourceStream } from "@/utils/APIHelper"
import { setRcaStatus } from "../ZonesModal/ZonesModal"
import List from "@/components/List/List"
import ListItem from "../List/ListItem/ListItem"

import PropTypes from "prop-types";

const LIST_ITEM_FONT_SIZE = "1.5rem"

let applyAction = null

export const executeApplyAction = () => {
  if (applyAction !== null) {
    const temp = applyAction
    applyAction = null
    return temp()
  }
}

const StreamsModal = ({
  sourceId,
  onApply,
  onClose,
  applyImmediately,
}) => {
  const streams = useStatusStore((state) => state.status.streams)
  const status = useStatusStore((state) => state.status)

  const setStream = (stream) => {
    const streamId = stream.id
    let currentSourceId = sourceId
    // RCA can only be used on its associated source, so swap if necessary
    const moveSource = stream.type === "rca" && stream.index != sourceId
    if (moveSource) {
      currentSourceId = stream.index
      // notify ZonesModal that we are using a different sourceId
      setRcaSourceId(currentSourceId)
      // move whatever is here to the original source
    }

    const apply = () => {
      if (moveSource) {
        // move then set new stream
        const statusModified = JSON.parse(JSON.stringify(status))
        return moveSourceContents(status, currentSourceId, sourceId).then(
          () => {
            statusModified.zones.forEach((z) => {
              if (z.source_id === currentSourceId) {
                z.source_id = sourceId
              }
            })
            setRcaStatus(statusModified)
            console.log(`move source. streamId: ${streamId}`)
            setSourceStream(currentSourceId, streamId)
          }
        )
      } else {
        // just set new stream
        console.log(`not move source. streamId: ${streamId}`)
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
          setStream(stream)
          onApply()
          onClose()
        }}
        nameFontSize={LIST_ITEM_FONT_SIZE}
      >
        <img src={icon} className="streams-modal-icon" alt="stream icon" />
      </ListItem>
    )
  }

  return (
    <ModalCard header="Select Stream" onClose={onClose} onCancel={onClose}>
      <List>{streamsList}</List>
    </ModalCard>
  );
};
StreamsModal.propTypes = {
    setStreamModalOpen: PropTypes.func.isRequired,
    sourceId: PropTypes.any.isRequired,
    onApply: PropTypes.func,
    onClose: PropTypes.func,
    applyImmediately: PropTypes.bool,
};
StreamsModal.defaultProps = {
    onApply: () => {},
    onClose: () => {},
    applyImmediately: true,
};

export default StreamsModal