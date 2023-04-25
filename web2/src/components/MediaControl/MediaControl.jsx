import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faStepBackward } from "@fortawesome/free-solid-svg-icons"
import { faStepForward } from "@fortawesome/free-solid-svg-icons"
import { faPause } from "@fortawesome/free-solid-svg-icons"
import { faPlay } from "@fortawesome/free-solid-svg-icons"
import { faStop } from "@fortawesome/free-solid-svg-icons"

import { useStatusStore } from "@/App.jsx"

import "./MediaControl.scss"

const MediaControl = ({ selectedSource }) => {
  // const source = status.sources[selectedSource]
  const source = useStatusStore((s) => s.status.sources[selectedSource])

  const enabled = "media-control"
  const disabled = "media-control media-control-disabled"
  const streamId = source.input.split("=")[1] // TODO: what if this is rca? or is rca a stream now

  const setSourceState = (state) => {} // TODO

  const playing = source.info.state.includes("playing")
  const isSupported = (cmd) => source.info.supported_cmds.includes(cmd)
  const postCommand = (cmd) => {
    fetch(`/api/streams/${streamId}/${cmd}`, {
      method: "POST",
      headers: {
        "Content-type": "application/json",
      },
    })
  }

  const Center = (() => {
    if (playing) {
      if (isSupported("pause")) {
        return (
          <FontAwesomeIcon
            icon={faPause}
            className={enabled}
            onClick={() => {
              postCommand("pause")
              setSourceState("paused")
            }}
          />
        )
      } else if (isSupported("stop")) {
        return (
          <FontAwesomeIcon
            icon={faStop}
            className={enabled}
            onClick={() => {
              postCommand("stop")
              setSourceState("stopped")
            }}
          />
        )
      } else {
        return <FontAwesomeIcon icon={faStop} className={disabled} />
      }
    } else {
      if (isSupported("play")) {
        return (
          <FontAwesomeIcon
            icon={faPlay}
            className={enabled}
            onClick={() => {
              postCommand("play")
              setSourceState("playing")
            }}
          />
        )
      } else {
        return <FontAwesomeIcon icon={faPlay} className={disabled} />
      }
    }
  })()

  const cmdToClassName = (cmd) => (isSupported(cmd) ? enabled : disabled)

  const Backward = (
    <FontAwesomeIcon
      icon={faStepBackward}
      className={cmdToClassName("prev")}
      onClick={() => postCommand("prev")}
    />
  )
  const Forward = (
    <FontAwesomeIcon
      icon={faStepForward}
      className={cmdToClassName("next")}
      onClick={() => postCommand("next")}
    />
  )

  return (
    <div className="media-outer">
      <div className="media-inner">
        {Backward}
        {Center}
        {Forward}
      </div>
    </div>
  )
}

export default MediaControl
