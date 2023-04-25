import PageHeader from "@/components/PageHeader/PageHeader"
import "./Presets.scss"
import { useStatusStore } from "@/App.jsx"
import { useState } from "react"
import { Fab } from "@mui/material"
import AddIcon from "@mui/icons-material/Add"
import CreatePresetModal from './CreatePresetModal/CreatePresetModal'
import EditPresetModal from "./EditPresetModal/EditPresetModal"


const PresetListItem = ({ preset }) => {
  const [presetOpen, setPresetOpen] = useState(false);

  return (
    <>
      <div onClick={()=>setPresetOpen(true)}>
        {preset.name}
      </div>
      { presetOpen &&
        <EditPresetModal onClose={()=>setPresetOpen(false)} preset={preset}/>
      }
    </>
  )
}

const Presets = ({ onClose }) => {
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const presets = useStatusStore((s) => s.status.presets)

  const presetListItems = presets.map((preset) => {
    return <PresetListItem preset={preset} key={preset.id} />
  })

  return (
    <>
      <PageHeader title="Presets" onClose={onClose} />
      <div className="presets-body">{presetListItems}</div>
      <div className="add-preset-button">
        <Fab
          onClick={() => {
            setCreateModalOpen(true);
          }}
        >
          <AddIcon></AddIcon>
        </Fab>
      </div>
      {createModalOpen && <CreatePresetModal onClose={()=>setCreateModalOpen(false)}/>}
    </>
  )
}

export default Presets
