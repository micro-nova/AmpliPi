import "./ZonesModal.scss"
import Modal from "../Modal/Modal"
import Card from "../Card/Card"
import Checkbox from "@mui/material/Checkbox"
import { useEffect, useState } from "react"
import { IconButton } from "@mui/material"
import DoneIcon from "@mui/icons-material/Done"
import { width } from "@mui/system"
import { useStatusStore } from "@/App.jsx"
import { getSourceZones } from "@/pages/Home/Home"
import SpeakerIcon from '@mui/icons-material/Speaker';
import SpeakerGroupIcon from '@mui/icons-material/SpeakerGroup';

const ZonesModal = ({ sourceId, setZoneModalOpen, onClose }) => {
  const zones = useStatusStore
    .getState()
    .status.zones.filter((zone) => !zone.disabled)
  const groups = useStatusStore.getState().status.groups
  const [checkedZones, setCheckedZones] = useState(
    zones
      .map((zone) => {
        if (zone.source_id == sourceId) {
          return zone.id
        }
      })
      .filter((item) => {
        return item != undefined
      })
  )
  const [checkedGroups, setCheckedGroups] = useState(
    groups
      .map((group) => {
        if (group.source_id == sourceId) {
          return group.id
        }
      })
      .filter((item) => {
        return item != undefined
      })
  )

  const handleChangeZone = (id) => {
    if (checkedZones.includes(id)) {
      let newList = checkedZones.filter((item) => item != id)
      setCheckedZones(newList)
    } else {
      setCheckedZones([...checkedZones, id])
    }
  }

  const handleChangeGroup = (id) => {
    if (checkedGroups.includes(id)) {
      let newList = checkedGroups.filter((item) => item != id)
      setCheckedGroups(newList)
    } else {
      setCheckedGroups([...checkedGroups, id])
    }
  }

  const ZonesModalZoneItem = ({ zone, selectable, defaultSelected }) => {
    return (
      <div className="zones-modal-list-item" key={zone.id}>
        {selectable && (
          <Checkbox
            onChange={() => handleChangeZone(zone.id)}
            defaultChecked={defaultSelected}
          />
        )}
        <div className="zone-icon">
          <SpeakerIcon />
        </div>
        {zone.name}
      </div>
    )
  }

  const ZonesModalGroupItem = ({ group, selectable, defaultSelected }) => {
    return (
      <div className="zones-modal-list-item" key={group.id}>
        {selectable && (
          <Checkbox
            onChange={() => handleChangeGroup(group.id)}
            defaultChecked={defaultSelected}
          />
        )}
        <div className="group-icon">
          <SpeakerGroupIcon />
        </div>
        {group.name}
      </div>
    )
  }

  const setZones = () => {
    let removeList = []
    let addList = []

    for (const zone of zones.filter((zone) => {
      return zone.source_id == sourceId
    })) {
      if (!checkedZones.includes(zone.id)) {
        removeList.push(zone.id)
      }
    }

    for (const zone of zones.filter((zone) => {
      return zone.source_id != sourceId
    })) {
      if (checkedZones.includes(zone.id)) {
        addList.push(zone.id)
      }
    }

    fetch(`/api/zones`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({ zones: removeList, update: { source_id: -1 } }),
    })

    fetch(`/api/zones`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({
        zones: addList,
        update: { mute: false, source_id: sourceId },
      }),
    })
  }

  const setGroups = () => {
    let removeList = []
    let addList = []

    for (const group of groups.filter((group) => {
      return group.source_id == sourceId
    })) {
      if (!checkedGroups.includes(group.id)) {
        removeList.push(group.id)
      }
    }

    for (const group of groups.filter((group) => {
      return group.source_id != sourceId
    })) {
      if (checkedGroups.includes(group.id)) {
        addList.push(group.id)
      }
    }

    for (const i of removeList) {
      fetch(`/api/groups/${i}`, {
        method: "PATCH",
        headers: {
          "Content-type": "application/json",
        },
        body: JSON.stringify({ source_id: -1 }),
      })
    }

    for (const i of addList) {
      fetch(`/api/groups/${i}`, {
        method: "PATCH",
        headers: {
          "Content-type": "application/json",
        },
        body: JSON.stringify({ source_id: sourceId, mute: false }),
      })
    }
  }

  const groupItems = groups.map((group) => {
    let selected = false
    if (group.source_id == sourceId) {
      selected = true
    }
    return ZonesModalGroupItem({
      group: group,
      selectable: true,
      defaultSelected: selected,
    })
  })

  const zoneItems = zones.map((zone) => {
    let selected = false
    if (zone.source_id == sourceId) {
      selected = true
    }
    return ZonesModalZoneItem({
      zone: zone,
      selectable: true,
      defaultSelected: selected,
    })
  })

  return (
    <Modal className="zones-modal" onClose={onClose}>
      <Card className="zones-modal-card">
        <div className="zones-modal-header">Select Zones</div>
        <div className="zones-modal-body">
          {groupItems}
          {zoneItems}
        </div>
        <div className="zones-modal-footer">
          <IconButton
            onClick={() => {
              setZones()
              setGroups()
              setZoneModalOpen(false)
            }}
          >
            <DoneIcon
              className="zones-modal-button-icon"
              style={{ width: "3rem", height: "3rem" }}
            />
          </IconButton>
        </div>
      </Card>
    </Modal>
  )
}

export default ZonesModal
