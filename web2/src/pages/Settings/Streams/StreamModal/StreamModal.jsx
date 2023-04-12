import { useState } from "react"
import Modal from '@/components/Modal/Modal'
import Card from '@/components/Card/Card'
import { IconButton } from "@mui/material"
import DoneIcon from '@mui/icons-material/Done'
import DeleteIcon from '@mui/icons-material/Delete'
import './StreamModal.scss'
import StreamTemplates from '../StreamTemplates.json'

const NAME_DESC = "This name can be anything - it will be used to select this stream from the source selection dropdown"
const DISABLED_DESC = "Don't show this stream in the input dropdown"

const TextField = ({name, desc, defaultValue, onChange}) => {
  return (
    <div className='stream-field'>
      <div className='stream-field-name'>{name}</div>
      <input type="text" defaultValue={defaultValue} onChange={(e)=>{onChange(e.target.value)}}/>
      <div className='stream-field-desc'>{desc}</div>
    </div>)
};

const BoolField = ({name, desc, defaultValue, onChange}) => {
  return (
    <div className='stream-field'>
      <div className='stream-field-name'>{name}</div>
      <input type="checkbox" defaultChecked={defaultValue} onChange={(e)=>{onChange(e.target.checked)}}/>
      <div className='stream-field-desc'>{desc}</div>
    </div>)
};

const StreamModal = ({stream, onClose, apply, del}) => {
  const [streamFields, setStreamFields] = useState(JSON.parse(JSON.stringify(stream))) // set streamFields to copy of stream

  const streamTemplate = StreamTemplates.filter((t)=>t.type===stream.type)[0]

  return (
    <Modal onClose={onClose}>
      <Card className="stream-card">
        <div>
          <div className='stream-name'>
            {stream.name}
          </div>

          <div>
            <TextField name="Name" desc={NAME_DESC} defaultValue={streamFields.name} onChange={(v)=>{setStreamFields({...streamFields, 'name': v})}}/>
            {
              // Render fields from StreamFields.json
              streamTemplate.fields.map((field) => {
                switch (field.type) {
                  case 'text':
                    return <TextField key={field.name} name={field.name} desc={field.desc} required={field.required} defaultValue={streamFields[field.name]} onChange={(v)=>{setStreamFields({...streamFields, [field.name]: v})}}/>
                  case 'bool':
                    return <BoolField key={field.name} name={field.name} desc={field.desc} defaultValue={streamFields[field.name]} onChange={(v)=>{setStreamFields({...streamFields, [field.name]: v})}}/>
                }
              })
            }
            <BoolField name="Disable" desc={DISABLED_DESC} defaultValue={streamFields.disabled} onChange={(v)=>{setStreamFields({...streamFields, 'disabled': v})}}/>
          </div>
        </div>
        <div className="stream-buttons">
          <IconButton onClick={()=>{apply(streamFields); onClose()}}> <DoneIcon className="stream-button-icon" style={{width:"3rem", height:"3rem"}}/> </IconButton>
          <IconButton onClick={()=>{if(del) del(streamFields); onClose()}}> <DeleteIcon className="stream-button-icon" style={{width:"3rem", height:"3rem"}}/> </IconButton>
        </div>
      </Card>
    </Modal>
  )
}

export default StreamModal
