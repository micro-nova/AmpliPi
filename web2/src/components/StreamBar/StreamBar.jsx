import './StreamBar.scss'
import spotify from '@/assets/spotify.png'

import { useStatusStore } from '@/App.jsx'

const StreamBar = ({ sourceId }) => {
    const nametype = useStatusStore(state => state.status.streams[sourceId].name).split(' - ')
    const type = nametype[1]
    const name = nametype[0]

    const icon = spotify
      //TODO: populate this with icons or add endpoint to get icons
      // code will be shared with StreamBadge, should be put somewhere else and imported
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