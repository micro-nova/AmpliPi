import PageHeader from "@/components/PageHeader/PageHeader"
import "../PageBody.scss"
import "./Groups.scss"
import { useStatusStore } from "@/App.jsx"
import { useState } from "react"
import { Divider, Fab } from "@mui/material"
import AddIcon from "@mui/icons-material/Add"
import GroupModal from "./GroupModal/GroupModal"
import { SpeakerGroup } from "@mui/icons-material"
import List from "@/components/List/List"
import ListItem from "@/components/List/ListItem/ListItem"

const GroupListItem = ({ group, zones }) => {
  const [modalOpen, setModalOpen] = useState(false)

  const editGroup = (name, zones) => {
    fetch("/api/groups/" + group.id, {
      method: "PATCH",
      headers: { "Content-type": "application/json" },
      body: JSON.stringify({ name: name, zones: zones }),
    })
  }

  const deleteGroup = () => {
    fetch("/api/groups/" + group.id, { method: "DELETE" })
  }

  return (
    <ListItem name={group.name} onClick={() => {
      setModalOpen(true)
    }}>
      <div className="groups-group-icon">
        <SpeakerGroup fontSize="inherit"/>
      </div>
      {modalOpen && (
        <GroupModal
          group={group}
          zones={zones}
          onClose={() => {
            setModalOpen(false)
          }}
          del={deleteGroup}
          apply={editGroup}
        />
      )}
    </ListItem>
  )
}

const addGroup = (name, zones) => {
  fetch("/api/group", {
    method: "POST",
    headers: { "Content-type": "application/json" },
    body: JSON.stringify({ name: name, zones: zones }),
  })
}

const Groups = ({ onClose }) => {
  const groups = useStatusStore((s) => s.status.groups)
  const zones = useStatusStore((s) => s.status.zones)
  const [modalOpen, setModalOpen] = useState(false)

  let groupsListItems = groups.map((group) => {
    return <GroupListItem key={group.id} group={group} zones={zones} />
  })

  return (
    <div className="page-container">
      <PageHeader title="Groups" onClose={onClose} />
      <div className="page-body">
      <List>
        {groupsListItems}
      </List>
      </div>
      <div className="add-button">
        <Fab
          onClick={() => {
            setModalOpen(true)
          }}
        >
          <AddIcon></AddIcon>
        </Fab>
      </div>
      {modalOpen && (
        <GroupModal
          group={{ name: "New Group", zones: [] }}
          zones={zones}
          onClose={() => setModalOpen(false)}
          apply={addGroup}
        />
      )}
    </div>
  )
}

export default Groups
