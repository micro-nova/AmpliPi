import PageHeader from "@/components/PageHeader/PageHeader"
import "../PageBody.scss"
import "./Presets.scss"
import { useStatusStore } from "@/App.jsx"
import { useState } from "react"
import { Fab, Divider } from "@mui/material"
import AddIcon from "@mui/icons-material/Add"
import CreatePresetModal from "./CreatePresetModal/CreatePresetModal"
import EditPresetModal from "./EditPresetModal/EditPresetModal"
import {PlaylistAdd} from "@mui/icons-material"

const PresetListItem = ({ preset }) => {
  const [presetOpen, setPresetOpen] = useState(false)

  return (
    <>
      <div className="presets-item-container" onClick={() => setPresetOpen(true)}>
        <div className="presets-item-icon"><PlaylistAdd fontSize="inherit" /></div>
        {preset.name}
      </div>

      <Divider/>
      {presetOpen && (
        <EditPresetModal onClose={() => setPresetOpen(false)} preset={preset} />
      )}
    </>
  )
}

const Presets = ({ onClose }) => {
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const presets = useStatusStore((s) => s.status.presets)

  const presetListItems = presets.map((preset) => (
    <PresetListItem preset={preset} key={preset.id} />
  ))

  return (
    <div className="page-container">
      <PageHeader title="Presets" onClose={onClose} />
      <div className="page-body">{presetListItems}</div>
      <div className="add-button">
        <Fab
          onClick={() => {
            setCreateModalOpen(true)
          }}
        >
          <AddIcon />
        </Fab>
      </div>
      {createModalOpen && (
        <CreatePresetModal onClose={() => setCreateModalOpen(false)} />
      )}
    </div>
  )
}

export default Presets
