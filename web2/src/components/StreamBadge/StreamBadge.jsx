import './StreamBadge.scss'
import { useStatusStore, getIcon } from '@/App.jsx'

const StreamBadge = ({ sourceId }) => {
  const info = useStatusStore((s) => s.status.sources[sourceId].info)
  const name = info.name.split(" - ")[0]
  const type = info.name.split(" - ")[1]

  const icon = getIcon(type);

  return (
    <div className="stream-badge">
      <div className="stream-badge-name">
      {name}
      </div>
        <img src={icon} className="stream-badge-icon" alt="stream icon" />
    </div>
  );
}

export default StreamBadge
