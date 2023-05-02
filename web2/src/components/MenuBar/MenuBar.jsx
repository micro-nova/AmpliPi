import "./MenuBar.scss"
import BottomNavigation from "@mui/material/BottomNavigation"
import BottomNavigationAction from "@mui/material/BottomNavigationAction"
import HomeIcon from "@mui/icons-material/Home"
import AlbumIcon from "@mui/icons-material/Album"
import SettingsIcon from "@mui/icons-material/Settings"
import QueueMusicIcon from "@mui/icons-material/QueueMusic"
import Badge from "@mui/material/Badge"
import { useStatusStore, usePersistentStore } from "@/App"

const MenuBar = ({ onChange, pageNumber }) => {
  const updateAvailable = useStatusStore(
    (s) =>
      s.status.info.version
        .split("+")[0]
        .localeCompare(s.status.info.latest_release, undefined, {
          numeric: true,
          sensitivity: "base",
        }) < 0
  )

  const selectedSource = usePersistentStore((s) => s.selectedSource)
  const sourceIsStopped = useStatusStore(s => s.status.sources[selectedSource].info.state) === 'stopped'

  return (
    <div className="bar">
      <BottomNavigation
        value={pageNumber}
        onChange={(event, num) => {
          onChange(num)
        }}
      >
        <BottomNavigationAction label="Home" icon={<HomeIcon />} />
        {!sourceIsStopped && <BottomNavigationAction label="Player" icon={<AlbumIcon />} />}
        { false && <BottomNavigationAction label="Browser" icon={<QueueMusicIcon />} />}
        <BottomNavigationAction
          label="Settings"
          icon={
            <Badge badgeContent={updateAvailable ? " " : null} color="primary">
              <SettingsIcon />
            </Badge>
          }
        />
      </BottomNavigation>
    </div>
  )
}

export default MenuBar
