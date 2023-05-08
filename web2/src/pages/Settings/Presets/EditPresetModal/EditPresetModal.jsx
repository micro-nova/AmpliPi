import { useState } from "react"

import Modal from "@/components/Modal/Modal"
import Card from "@/components/Card/Card"
import DoneIcon from "@mui/icons-material/Done"
import DeleteIcon from "@mui/icons-material/Delete"
import IconButton from "@mui/material/IconButton"
import "./EditPresetModal.scss"
import ModalCard from "@/components/ModalCard/ModalCard.jsx";

const EditPresetModal = ({ onClose, preset }) => {
  const [name, setName] = useState(preset.name)

  const editPreset = () => {
    const preset_copy = JSON.parse(JSON.stringify(preset))
    preset_copy.name = name
    fetch(`/api/presets/${preset.id}`, {
      method: "PATCH",
      headers: { "Content-type": "application/json" },
      body: JSON.stringify(preset_copy),
    })
  }

  const deletePreset = () => {
    fetch(`/api/presets/${preset.id}`, { method: "DELETE" })
  }

  return (
    <ModalCard
      onClose={onClose}
      onDelete={() => {
        deletePreset()
        onClose()
      }}
      onAccept={() => {
        editPreset()
        onClose()
      }}
    >
      <div className="preset-name">Edit Preset</div>
      <div className="preset-name-input-container">
        <div>Name</div>
        <input
          className="preset-name-input"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
    </ModalCard>
  )
}

export default EditPresetModal
