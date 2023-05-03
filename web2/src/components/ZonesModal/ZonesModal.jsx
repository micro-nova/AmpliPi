import "./ZonesModal.scss"
import ModalCard from '@/components/ModalCard/ModalCard'
import Checkbox from "@mui/material/Checkbox"
import { useState } from "react"
import { IconButton } from "@mui/material"
import DoneIcon from "@mui/icons-material/Done"
import { useStatusStore } from "@/App.jsx"
import SpeakerIcon from '@mui/icons-material/Speaker'
import SpeakerGroupIcon from '@mui/icons-material/SpeakerGroup'

const ZonesModal = ({ sourceId, onApply=()=>{}, onClose=()=>{}, loadZonesGroups=true }) => {
  const zones = useStatusStore
    .getState()
    .status.zones.filter((zone) => !zone.disabled)
  const groups = useStatusStore.getState().status.groups
  const [checkedZonesIds, setCheckedZoneIds] = useState(
    zones
    .filter((zone) => zone.source_id === sourceId && loadZonesGroups)
    .map((zone) => zone.id)
  )
  const [checkedGroupIds, setCheckedGroupIds] = useState(
    groups
    .filter((group) => group.source_id === sourceId && loadZonesGroups)
    .map((group) => group.id)
  )

  const computeCheckedGroups = (newCheckedZonesIds) => {
    let newGroups = []
    // groups.forEach(g => {
    //   if (g.zones.every(id => checkedZonesIds.includes(id))) {
    //     newGroups.push(g.id)
    //   }
    // })

    newGroups = groups.filter(g => g.zones.every(id => newCheckedZonesIds.includes(id))).map(g => g.id)

    setCheckedGroupIds(newGroups)
  }

  const handleChangeZone = (id) => {
    let newZones = [...checkedZonesIds]
    if (checkedZonesIds.includes(id)) {
      // currently checked. uncheck
      newZones = newZones.filter(item => item != id)
    } else {
      // currently unchecked. check
      newZones.push(id)
    }
    setCheckedZoneIds(newZones)
    // TODO: recompute checked groups
    computeCheckedGroups(newZones)
  }

  const handleChangeGroup = (id) => {
    const group = groups.filter(g => g.id === id)[0]
    let newZones = [...checkedZonesIds]

    if (checkedGroupIds.includes(id)) {
      // currently checked. unckeck associated zones
      group.zones.forEach(zid => newZones = newZones.filter(new_zid => new_zid !== zid))
    } else {
      // currently unchecked. check associated zones
      group.zones.forEach(zid => {
        if (!newZones.includes(zid)) newZones.push(zid)
      })
    }
    setCheckedZoneIds(newZones)

    // TODO: recompute checked groups
    computeCheckedGroups(newZones)
  }

  const ZonesModalZoneItem = ({ zone, defaultSelected, checked }) => {
    return (
      <div className="zones-modal-list-item" key={zone.id}>
        <Checkbox
          checked={checked}
          onChange={() => handleChangeZone(zone.id)}
          defaultChecked={defaultSelected}
        />
        <div className="zone-icon">
          <SpeakerIcon />
        </div>
        {zone.name}
      </div>
    )
  }

  const ZonesModalGroupItem = ({ group, defaultSelected, checked }) => {
    return (
      <div className="zones-modal-list-item" key={group.id}>
        <Checkbox
          checked={checked}
          onChange={() => handleChangeGroup(group.id)}
          defaultChecked={defaultSelected}
        />
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
      if (!checkedZonesIds.includes(zone.id)) {
        removeList.push(zone.id)
      }
    }

    for (const zone of zones.filter((zone) => {
      return zone.source_id != sourceId
    })) {
      if (checkedZonesIds.includes(zone.id)) {
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
      if (!checkedGroupIds.includes(group.id)) {
        removeList.push(group.id)
      }
    }

    for (const group of groups.filter((group) => {
      return group.source_id != sourceId
    })) {
      if (checkedGroupIds.includes(group.id)) {
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
    const checked = checkedGroupIds.includes(group.id)
    if (group.source_id == sourceId) {
      selected = true
    }
    return ZonesModalGroupItem({
      group: group,
      checked: checked,
      defaultSelected: selected,
    })
  })

  const zoneItems = zones.map((zone) => {
    let selected = false
    const checked = checkedZonesIds.includes(zone.id)
    if (zone.source_id == sourceId) {
      selected = true
    }
    return ZonesModalZoneItem({
      zone: zone,
      checked: checked,
      defaultSelected: selected,
    })
  })

  return (
    <ModalCard onClose={onClose} header="Select Zones">
      <div className="zones-modal-body">
        {groupItems}
        {zoneItems}
      </div>
      <div className="zones-modal-footer">
        <IconButton
          onClick={() => {
            setZones()
            setGroups()
            onApply()
            onClose()
          }}
        >
          <DoneIcon
            className="zones-modal-button-icon"
            style={{ width: "3rem", height: "3rem" }}
          />
        </IconButton>
      </div>
    </ModalCard>
  )
}

export default ZonesModal
