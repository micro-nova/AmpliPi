import './StreamBadge.scss'
import spotify from '@/assets/spotify.png'

const StreamBadge = ({ info }) => {
  info = info.name.split(" - ")
  const name = info[0]
  const type = info[1]

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
