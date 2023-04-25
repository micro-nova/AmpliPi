import StreamBar from "@/components/StreamBar/StreamBar"
import SongInfo from "@/components/SongInfo/SongInfo"
import MediaControl from "@/components/MediaControl/MediaControl"
import "./Player.scss"
import { useStatusStore } from "@/App.jsx"
import CardVolumeSlider from "@/components/CardVolumeSlider/CardVolumeSlider"
import { IconButton } from "@mui/material"
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown"
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp"
import { useState } from "react"
import VolumeZones from "@/components/VolumeZones/VolumeZones"
import Card from "@/components/Card/Card"

const Player = ({ }) => {
  const selectedSource = useStatusStore((s) => s.selectedSource)
  const img_url = useStatusStore(
    (s) => s.status.sources[selectedSource].info.img_url
  )
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      <StreamBar sourceId={selectedSource}></StreamBar>
      <div className="player-outer">
        <div className="player-inner">
          <img src={img_url} className="player-album-art" />
          <SongInfo
            sourceId={selectedSource}
            artistClassName="player-info-title"
            albumClassName="player-info-album"
            trackClassName="player-info-track"
          />
          <MediaControl selectedSource={selectedSource} />
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
        </div>
      </div>
      {expanded && <VolumeZones sourceId={selectedSource} />}
    </>
  )
}

export default Player
