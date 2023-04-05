import './StreamBadge.scss'
import spotify from '@/assets/spotify.png'
import { useStatusStore } from '@/App.jsx'

const StreamBadge = ({ sourceId }) => {
  const info = useStatusStore((s) => s.status.sources[sourceId].info)
  const name = info.name.split(" - ")[0]
  const type = info.name.split(" - ")[1]

  const icon = spotify
  //TODO: populate this with icons or add endpoint to get icons
  switch (type) {
  }

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
