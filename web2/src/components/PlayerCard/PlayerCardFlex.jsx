import Card from "@/components/Card/Card"
import "./PlayerCard.scss"
import StreamBadge from "@/components/StreamBadge/StreamBadge"
import SongInfo from "../SongInfo/SongInfo"
import CardVolumeSlider from "../CardVolumeSlider/CardVolumeSlider"
import { useState } from "react"
import PlayerImage from "../PlayerImage/PlayerImage"
import ZonesBadge from "../ZonesBadge/ZonesBadge"
import StreamsModal from "../StreamsModal/StreamsModal"
import ZonesModal from "../ZonesModal/ZonesModal"
import { usePersistentStore } from "@/App.jsx"
import { router } from "@/main"

const PlayerCardFlex = ({ sourceId }) => {
  const [streamModalOpen, setStreamModalOpen] = useState(false)
  const [zoneModalOpen, setZoneModalOpen] = useState(false)
  const setSelectedSource = usePersistentStore((s) => s.setSelectedSource)
  const selected = usePersistentStore((s) => s.selectedSource) === sourceId

  const select = () => {
    if (selected) {
      router.navigate("/player")
    }

    setSelectedSource(sourceId)
  }

  return (
    <Card selected={selected}>
      <div className="top">
        <div className="">

        </div>
        <div className="vol">

        </div>
      </div>
    </Card>
  )
}

export default PlayerCardFlex
