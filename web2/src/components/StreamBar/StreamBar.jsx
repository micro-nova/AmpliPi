import './StreamBar.scss'
import spotify from '@/assets/spotify.png'

const StreamBar = ({ info }) => {
    info = info.name.split(" - ")
    const name = info[0]
    const type = info[1]

    const icon = spotify
      //TODO: populate this with icons or add endpoint to get icons
      // code will be shared with SteamBadge, should be put somewhere else and imported
    return (
        <div className="stream-bar">
            <div className="stream-bar-name">
                {name}
            </div>
            <img src={icon} className="stream-bar-icon" alt="stream icon" />
        </div>
    )
}

export default StreamBar