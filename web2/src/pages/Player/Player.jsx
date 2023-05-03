import StreamBar from "@/components/StreamBar/StreamBar"
import SongInfo from "@/components/SongInfo/SongInfo"
import MediaControl from "@/components/MediaControl/MediaControl"
import "./Player.scss"
import { useStatusStore, usePersistentStore } from "@/App.jsx"
import CardVolumeSlider from "@/components/CardVolumeSlider/CardVolumeSlider"
import { IconButton } from "@mui/material"
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown"
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp"
import { useState } from "react"
import VolumeZones from "@/components/VolumeZones/VolumeZones"
import Card from "@/components/Card/Card"

const Player = ({ }) => {
  const selectedSource = usePersistentStore((s) => s.selectedSource)
  // TODO: dont index into sources. id isn't guarenteed to line up with order
  const img_url = useStatusStore(
    (s) => s.status.sources[selectedSource].info.img_url
  )
  const sourceIsStopped = useStatusStore(s => s.status.sources[selectedSource].info.state) === 'stopped'
  const [expanded, setExpanded] = useState(false)

  if (sourceIsStopped) {
    return (
      <div className="player-outer">
        <div className="player-stopped-message">No Player Selected!</div>
      </div>
    
    )
  }

  return (
    <div className="player-outer">
      <StreamBar sourceId={selectedSource} />
      <div className="player-inner">
        <img src={img_url} className="player-album-art" />
        <SongInfo
          sourceId={selectedSource}
          artistClassName="player-info-title"
          albumClassName="player-info-album"
          trackClassName="player-info-track"
        />
        <MediaControl selectedSource={selectedSource} />
      </div>

      <Card className="player-volume-slider">
        <CardVolumeSlider sourceId={selectedSource} />
        <IconButton onClick={() => setExpanded(!expanded)}>
          {expanded ? (
          <KeyboardArrowUpIcon
            className="player-volume-expand-button"
            style={{ width: "3rem", height: "3rem" }}
          />
          ) : (
            <KeyboardArrowDownIcon
              className="player-volume-expand-button"
              style={{ width: "3rem", height: "3rem" }}
            />
          )}
        </IconButton>
      </Card>
      {expanded && <VolumeZones sourceId={selectedSource} />}

    </div>
  )
}

export default Player
