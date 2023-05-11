import "./Zones.scss"
import "../PageBody.scss"
import { useStatusStore } from "@/App.jsx"
import { useState } from "react"
import PageHeader from "@/components/PageHeader/PageHeader"
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown"
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp"
import { Button } from "@mui/material"
import Speaker from "@mui/icons-material/Speaker"
import List from "@/components/List/List"
import ListItem from "@/components/List/ListItem/ListItem"

const ZoneListItem = ({ zone }) => {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState(zone.name)
  const [vol_max, setVolMax] = useState(zone.vol_max)
  const [vol_min, setVolMin] = useState(zone.vol_min)
  const [disabled, setDisabled] = useState(zone.disabled)

  const applyChanges = () => {
    fetch(`/api/zones/${zone.id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        name: name,
        vol_max: vol_max,
        vol_min: vol_min,
        disabled: disabled,
      }),
    })
  }

  return (
    <ListItem>
      <div className="zones-zone-column">
        <div className="zones-zone-row">
          <div className="zones-zone-icon">
            <Speaker fontSize="inherit" />
          </div>
          <div className="zones-zone-name">{zone.name}</div>
          <div className="zones-zone-expand-button">
            {open ? (
              <KeyboardArrowUpIcon
                className="zones-zone-expand-icon"
                fontSize="inherit"
                onClick={() => setOpen(!open)}
              />
            ) : (
              <KeyboardArrowDownIcon
                className="zones-zone-expand-icon"
                fontSize="inherit"
                onClick={() => setOpen(!open)}
              />
            )}
          </div>
        </div>
        {open && (
          <div className="zone-content-container">
            <div>
              Name:
              <input
                className="zones-input"
                type="text"
                name="Name"
                value={name}
                onChange={(e) => {
                  setName(e.target.value)
                }}
              />
            </div>
            <div>
              Max Volume:
              <input
                className="zones-input"
                type="text"
                name="Max Volume"
                value={vol_max}
                onChange={(e) => {
                  setVolMax(e.target.value)
                }}
              />
            </div>
            <div>
              Min Volume:
              <input
                className="zones-input"
                type="text"
                name="Min Volume"
                value={vol_min}
                onChange={(e) => {
                  setVolMin(e.target.value)
                }}
              />
            </div>
            <div>
              Disabled:
              <input
                className="zones-input"
                type="checkbox"
                name="Disabled"
                checked={disabled}
                onChange={(e) => {
                  setDisabled(e.target.checked)
                }}
              />
            </div>
            <div>
              <Button variant="contained" onClick={applyChanges}>
                Apply
              </Button>
            </div>
          </div>
        )}
      </div>
    </ListItem>
  )
}

const Zones = ({ onClose }) => {
  const zones = useStatusStore((state) => state.status.zones)

  const listItems = zones.map((zone) => {
    return <ZoneListItem zone={zone} key={zone.id} />
  })

  return (
    <div className="page-container">
      <PageHeader title="Zones" onClose={onClose} />
      <div className="page-body">
        <List>{listItems}</List>
      </div>
    </div>
  )
}

export default Zones
