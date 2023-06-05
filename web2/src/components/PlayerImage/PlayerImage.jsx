import "./PlayerImage.scss"
import { useStatusStore } from "@/App"

const PlayerImage = ({ sourceId }) => {
  const img_url = useStatusStore((s) => s.status.sources[sourceId].info.img_url)
  return <img src={img_url} className="image" />
}

export default PlayerImage
