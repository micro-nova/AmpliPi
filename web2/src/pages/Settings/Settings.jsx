import "./Settings.scss"
import Modal from "@/components/Modal/Modal"
import Streams from "./Streams/Streams"
import Zones from "./Zones/Zones"
import Groups from "./Groups/Groups"
import Sessions from "./Sessions/Sessions"
import Presets from "./Presets/Presets"
import Config from "./Config/Config"
import About from "./About/About"
import { router } from "@/main"
import Divider from "@mui/material/Divider"
import SpeakerIcon from "@mui/icons-material/Speaker"
import SpeakerGroupIcon from "@mui/icons-material/SpeakerGroup"
import VolumeUpIcon from "@mui/icons-material/VolumeUp"
import UpdateIcon from "@mui/icons-material/Update"
import HandymanIcon from "@mui/icons-material/Handyman"
import InfoIcon from "@mui/icons-material/Info"
import PlaylistAddIcon from "@mui/icons-material/PlaylistAdd"
import ListItem from "@/components/List/ListItem/ListItem"
import List from "@/components/List/List"

// TODO klayton: delete?
const PageListItem = ({ name, onClick, children }) => {
  return (
    <div className="settings-list-item" onClick={onClick}>
      <div className="settings-list-item-inner">
        {children} {name}
      </div>
      <Divider />
    </div>
  )
}

const close = () => router.navigate("/settings")

const CorePage = ({ openPage }) => {
  switch (openPage) {
    case "streams":
      return <Streams onClose={close} />
    case "zones":
      return <Zones onClose={close} />
    case "groups":
      return <Groups onClose={close} />
    case "sessions":
      return <Sessions onClose={close} />
    case "presets":
      return <Presets onClose={close} />
    case "config":
      return <Config onClose={close} />
    case "about":
      return <About onClose={close} />
    default:
      return <div></div>
  }
}

// wrap in modal if page is open
const Page = ({ openPage }) =>
  openPage === "" ? (
    <div />
  ) : (
    <Modal onClose={close}>
      <div className="settings-page-container">
        <CorePage openPage={openPage} />
      </div>
    </Modal>
  )

const Settings = ({ openPage = "" }) => {
  if (openPage != "") {
    return <Page openPage={openPage} />
  }

  return (
    <div className="settings-outer">
      <div className="settings-header">Settings</div>
      <div className="settings-body">
        <List>
          <ListItem
            name="Streams"
            onClick={() => router.navigate("/settings/streams")}
          >
            <div className="streams-icon">
              <VolumeUpIcon fontSize="inherit" />
            </div>
          </ListItem>

          <ListItem
            name="Zones"
            onClick={() => router.navigate("/settings/zones")}
          >
            <div className="zones-icon">
              <SpeakerIcon fontSize="inherit" />
            </div>
          </ListItem>

          <ListItem
            name="Groups"
            onClick={() => router.navigate("/settings/groups")}
          >
            <div className="groups-icon">
              <SpeakerGroupIcon fontSize="inherit" />
            </div>
          </ListItem>

          {/* <ListItem
            name="Sessions"
            onClick={() => router.navigate("/settings/sessions")}
          >
            <div className="sessions-icon"><CableIcon fontSize="inherit"/></div>
          </ListItem> */}

          <ListItem
            name="Presets"
            onClick={() => router.navigate("/settings/presets")}
          >
            <div className="presets-icon">
              <PlaylistAddIcon fontSize="inherit" />
            </div>
          </ListItem>

          <ListItem
            name="Configuration"
            onClick={() => router.navigate("/settings/config")}
          >
            <div className="config-icon">
              <HandymanIcon fontSize="inherit" />
            </div>
          </ListItem>

          <ListItem
            name="Updates"
            onClick={() => {
              window.location.href =
                "http://" + window.location.hostname + ":5001/update"
            }}
          >
            <div className="update-icon">
              <UpdateIcon fontSize="inherit" />
            </div>
          </ListItem>

          <ListItem
            name="About"
            onClick={() => router.navigate("/settings/about")}
          >
            <div className="about-icon">
              <InfoIcon fontSize="inherit" />
            </div>
          </ListItem>
        </List>
      </div>
    </div>
  )
}
export default Settings
