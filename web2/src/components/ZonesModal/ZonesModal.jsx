import "./ZonesModal.scss"
import ModalCard from "@/components/ModalCard/ModalCard"
import Checkbox from "@mui/material/Checkbox"
import { useState } from "react"
import { useStatusStore } from "@/App.jsx"
import SpeakerIcon from "@mui/icons-material/Speaker"
import SpeakerGroupIcon from "@mui/icons-material/SpeakerGroup"
import ListItem from "@/components/List/ListItem/ListItem.jsx"
import List from "@/components/List/List.jsx"

const LIST_ITEM_FONT_SIZE = "1.5rem"

// temp values used during rca operations
let useRcaSourceId = false
let rcaSourceId = -1
let rcaStatus = null

// called by StreamsModal when an rca is no longer being selected/configured
const clearRcaSourceId = () => {
  useRcaSourceId = false
  rcaSourceId = -1
  rcaStatus = null
}

// called by StreamsModal when an rca is selected
export const setRcaStatus = (status) => {
  rcaStatus = status
}

// called by StreamsModal when an rca is selected
export const setRcaSourceId = (id) => {
  rcaSourceId = id
  useRcaSourceId = true
}

const ZonesModal = ({
  sourceId,
  onApply = null,
  onClose = () => {},
  loadZonesGroups = true,
}) => {
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
    const newGroups = groups
      .filter((g) => g.zones.every((id) => newCheckedZonesIds.includes(id)))
      .map((g) => g.id)
    setCheckedGroupIds(newGroups)
  }

  const handleChangeZone = (id) => {
    let newZones = [...checkedZonesIds]
    if (checkedZonesIds.includes(id)) {
      // currently checked. uncheck
      newZones = newZones.filter((item) => item != id)
    } else {
      // currently unchecked. check
      newZones.push(id)
    }
    setCheckedZoneIds(newZones)
    computeCheckedGroups(newZones)
  }

  const handleChangeGroup = (id) => {
    const group = groups.filter((g) => g.id === id)[0]
    let newZones = [...checkedZonesIds]

    if (checkedGroupIds.includes(id)) {
      // currently checked. unckeck associated zones
      group.zones.forEach(
        (zid) => (newZones = newZones.filter((new_zid) => new_zid !== zid))
      )
    } else {
      // currently unchecked. check associated zones
      group.zones.forEach((zid) => {
        if (!newZones.includes(zid)) newZones.push(zid)
      })
    }
    setCheckedZoneIds(newZones)
    computeCheckedGroups(newZones)
  }

  const ZonesModalZoneItem = ({ zone, defaultSelected, checked }) => {
    return (
      <ListItem
        name={zone.name}
        nameFontSize={LIST_ITEM_FONT_SIZE}
        onClick={() => handleChangeZone(zone.id)}
        key={zone.id}
      >
        <Checkbox
          checked={checked}
          onChange={() => handleChangeZone(zone.id)}
        />
        <div className="zone-icon">
          <SpeakerIcon />
        </div>
      </ListItem>
    )
  }

  const ZonesModalGroupItem = ({ group, defaultSelected, checked }) => {
    return (
      <ListItem
        name={group.name}
        nameFontSize={LIST_ITEM_FONT_SIZE}
        onClick={() => handleChangeGroup(group.id)}
        key={group.id}
      >
        <Checkbox
          checked={checked}
          onChange={() => handleChangeGroup(group.id)}
        />
        <div className="group-icon">
          <SpeakerGroupIcon />
        </div>
      </ListItem>
    )
  }

  const setZones = () => {
    // redefine sourceId

    const sid = useRcaSourceId ? rcaSourceId : sourceId
    const zs = useRcaSourceId ? rcaStatus.zones : zones

    let removeList = []
    let addList = []

    for (const zone of zs.filter((zone) => {
      return zone.source_id == sid
    })) {
      if (!checkedZonesIds.includes(zone.id)) {
        removeList.push(zone.id)
      }
    }

    for (const zone of zs.filter((zone) => {
      return zone.source_id != sid
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
      body: JSON.stringify({
        zones: removeList,
        update: { source_id: -1 },
      }),
    })

    fetch(`/api/zones`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({
        zones: addList,
        update: { mute: false, source_id: sid },
      }),
    })
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
    <ModalCard
      onClose={onClose}
      onCancel={onClose}
      onAccept={() => {
        if (onApply !== null) {
          onApply().then(() => {
            setZones()
            onClose()
            clearRcaSourceId()
          })
        } else {
          setZones()
          onClose()
          clearRcaSourceId()
        }
      }}
      header="Select Zones"
    >
      <List>
        {groupItems}
        {zoneItems}
      </List>
    </ModalCard>
  )
}

export default ZonesModal
