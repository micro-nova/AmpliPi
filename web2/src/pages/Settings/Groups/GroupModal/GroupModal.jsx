import { useState } from "react"
import Modal from '@/components/Modal/Modal'
import Card from '@/components/Card/Card'
import { IconButton } from "@mui/material"
import DoneIcon from '@mui/icons-material/Done'
import DeleteIcon from '@mui/icons-material/Delete'
import { Select, MenuItem } from "@mui/material"
import './GroupModal.scss'

const GroupModal = ({ group, zones, onClose, del, apply }) => {
  const [groupName, setGroupName] = useState(group.name)
  const [groupZones, setGroupZones] = useState(group.zones)

  return (
    <Modal onClose={onClose}>
      <Card className="group-card">
        <div>
          <div className='group-name'>
            {group.name}
          </div>
          <input type="text" value={groupName} onChange={(e)=>{setGroupName(e.target.value)}}/>
          <br/>
          <Select className="group-multi" multiple defaultValue={groupZones} onChange={(e)=>{setGroupZones(e.target.value)}}>
            {zones.map((zone) => {
              return <MenuItem key={zone.id} value={zone.id}>{zone.name}</MenuItem>
            })}
          </Select>
          <div className="group-buttons">
          <IconButton onClick={()=>{del(); onClose()}}> <DeleteIcon className="group-button-icon" style={{width:"3rem", height:"3rem"}}/> </IconButton>
          <IconButton onClick={()=>{apply(groupName, groupZones); onClose()}}> <DoneIcon className="group-button-icon" style={{width:"3rem", height:"3rem"}}/> </IconButton>
          </div>
        </div>
      </Card>
    </Modal>
  )
}

export default GroupModal
