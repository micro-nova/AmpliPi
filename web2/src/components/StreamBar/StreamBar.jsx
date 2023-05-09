import "./StreamBar.scss"

import { useStatusStore } from "@/App.jsx"
import { getIcon } from "@/utils/getIcon"

const StreamBar = ({ sourceId }) => {
  const nametype = useStatusStore(
    (state) => state.status.sources[sourceId].info.name
  ).split(" - ")
  const type = nametype[1]
  const name = nametype[0]

  const icon = getIcon(type)
  //TODO: populate this with icons or add endpoint to get icons
  // code will be shared with StreamBadge, should be put somewhere else and imported
  return (
    <div className="stream-bar">
      <div className="stream-bar-name">{name}</div>
      <img src={icon} className="stream-bar-icon" alt="stream icon" />
    </div>
  )
}

export default StreamBar
