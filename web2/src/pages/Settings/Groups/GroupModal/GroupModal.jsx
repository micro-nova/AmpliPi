import { useState } from "react"
import ModalCard from '@/components/ModalCard/ModalCard'
import { IconButton } from "@mui/material"
import DoneIcon from "@mui/icons-material/Done"
import DeleteIcon from "@mui/icons-material/Delete"
import { Select, MenuItem } from "@mui/material"
import "./GroupModal.scss"
import Checkbox from "@mui/material/Checkbox"
import ListItemText from "@mui/material/ListItemText"

const getZoneNames = (zones, ids) => {
  return zones
    .filter((i) => {
      return ids.indexOf(i.id) > -1
    })
    .map((i) => {
      return i.name
    })
    .join(", ")
}

const GroupModal = ({ group, zones, onClose, del, apply }) => {
  const [groupName, setGroupName] = useState(group.name)
  const [groupZones, setGroupZones] = useState(group.zones)

  return (
    <ModalCard onClose={onClose} header="Edit Group">

      {/* <div className="group-name">{group.name}</div> */}
        <input
          type="text"
          value={groupName}
          onChange={(e) => {
            setGroupName(e.target.value)
          }}
        />
       <br />
      <Select
        className="group-multi"
        multiple
        defaultValue={groupZones}
        renderValue={(selected) => getZoneNames(zones, selected)}
        onChange={(e) => {
          setGroupZones(e.target.value)
        }}
      >
        {zones.map((zone) => {
          return (
            <MenuItem key={zone.id} value={zone.id}>
              <Checkbox checked={groupZones.indexOf(zone.id) > -1} />
              <ListItemText primary={zone.name} />
            </MenuItem>
          )
        })}
      </Select>
      <div className="group-buttons">
        <IconButton
          onClick={() => {
            if (del) del()
            onClose()
          }}
        >
          {" "}
          <DeleteIcon
            className="group-button-icon"
            style={{ width: "3rem", height: "3rem" }}
          />{" "}
        </IconButton>
        <IconButton
          onClick={() => {
            apply(groupName, groupZones)
            onClose()
          }}
        >
          {" "}
          <DoneIcon
            className="group-button-icon"
            style={{ width: "3rem", height: "3rem" }}
          />{" "}
        </IconButton>
      </div>
    </ModalCard>

  )
}

export default GroupModal
