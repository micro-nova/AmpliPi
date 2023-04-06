import StreamBar from '@/components/StreamBar/StreamBar'
import SongInfo from '@/components/SongInfo/SongInfo'
import MediaControl from '@/components/MediaControl/MediaControl'
import './Player.scss'
import { useStatusStore } from '@/App.jsx'
import VolumeSlider from '@/components/VolumeSlider/VolumeSlider'
import { IconButton } from '@mui/material'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { useState } from 'react'
import VolumesDrawer from '@/components/VolumesDrawer/VolumesDrawer'

const Player = ({ selectedSource }) => {
    const img_url = useStatusStore((s) => s.status.sources[selectedSource].info.img_url)
    const [drawerOpen, setDrawerOpen] = useState(false)

    return (
        <>
            <StreamBar sourceId={selectedSource}></StreamBar>
            <div className="player-outer">
                <div className="player-inner">
                    <img src={img_url} className="player-album-art" />
                    <SongInfo sourceId={selectedSource} artistClassName="player-info-title" albumClassName="player-info-album" trackClassName="player-info-track" />
                    <MediaControl selectedSource={selectedSource}/>
                    <div className='player-volume-slider'>
                      <VolumeSlider sourceId={selectedSource}/>
                      <IconButton onClick={()=>setDrawerOpen(!drawerOpen)}>
                        {
                          drawerOpen ? <KeyboardArrowUpIcon className='player-volume-expand-button' style={{width:"3rem", height:"3rem"}}/> :
                          <KeyboardArrowDownIcon className='player-volume-expand-button' style={{width:"3rem", height:"3rem"}}/>
                        }
                      </IconButton>
                    </div>
                </div>
              <VolumesDrawer open={drawerOpen} onClose={()=>setDrawerOpen(false)} sourceId={selectedSource}/>
            </div>
        </>
    )
}

export default Player
