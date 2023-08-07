import { LinkOff } from "@mui/icons-material"
import { useStatusStore } from "@/App"
import "./DisconnectedIcon.scss"

const DisconnectedIcon = () => {
  const connected = useStatusStore((s) => s.status.info.online)

  return (
    <div className="disconnected-icon">{connected ? null : <LinkOff />}</div>
  )
}

export default DisconnectedIcon
