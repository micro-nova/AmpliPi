import StreamBar from '@/components/StreamBar/StreamBar'
import SongInfo from '@/components/SongInfo/SongInfo'
import MediaControl from '@/components/MediaControl/MediaControl'
import './Player.scss'

const Player = ({ status, selectedSource }) => {
    const source = status.sources[selectedSource];
    // const zones = status.zones;

    return (
        <>
            <StreamBar info={source.info}></StreamBar>
            <div className="player-outer">
                <div className="player-inner">
                    <img src={source.info.img_url} className="player-album-art" />
                    <SongInfo info={source.info} artistClassName="player-info-title" albumClassName="player-info-album" trackClassName="player-info-track" />
                    <MediaControl source={source}/>
                </div>
            </div>
        </>
    )
}

export default Player