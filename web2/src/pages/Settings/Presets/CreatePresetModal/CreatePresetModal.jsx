import { useState } from "react"
import Modal from '@/components/Modal/Modal'
import Card from '@/components/Card/Card'
import DoneIcon from '@mui/icons-material/Done'
import './CreatePresetModal.scss'

import List from '@mui/material/List';
import ListSubheader from '@mui/material/ListSubheader';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Checkbox from '@mui/material/Checkbox';
import IconButton from '@mui/material/IconButton';
import Collapse from '@mui/material/Collapse';
import StarBorder from '@mui/icons-material/StarBorder';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Box from '@mui/material/Box';

const isEmpty = (dict) => Object.keys(dict).length === 0

const DictToTree = ({dict, depth=0}) => {
  if (isEmpty(dict)) return <div />
  console.log("DictToTree depth " + depth)

  // return <div> HELLOOOOOOOOOO</div>

  let entries = []
  let i = 0
  for (const [key, value] of Object.entries(dict)) {

    entries.push(
      <>
        <Box key={i} sx={{ display: 'flex', flexDirection: 'column', ml: 3*depth }}>
          <FormControlLabel
          label={key}
          control={<Checkbox />}
          />
          <DictToTree dict={value} depth={depth+1} />
        </Box>
      </>
    )

    i += 1
  }

  return entries

  return (
    <div>
      {Object.entries(dict).map((key, value) => {
        <Box sx={{ display: 'flex', flexDirection: 'column', ml: 3*depth }}>
          hi
          <FormControlLabel
          label={"HEY"}
          control={<Checkbox />}
          />
          {/* <DictToTree dict={value} depth={depth+1} /> */}
        </Box>
      })}
    </div>
  )

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', ml: 3*depth }}>
    {/* <FormControlLabel
      label="Child 1"
      control={<Checkbox checked={checked[0]} onChange={handleChange2} />}
    />
    <FormControlLabel
      label="Child 2"
      control={<Checkbox checked={checked[1]} onChange={handleChange3} />}
    /> */}
    {Object.entries(dict).map((key, value) => {
      <FormControlLabel
        label={key}
        control={<Checkbox />}
      />
    })}
    <DictToTree dict={label} depth={depth+1} />
  </Box>
  )

}

const CreatePresetModal = ({ onClose }) => {
  const [name, setName] = useState('name')

  const savePreset = () => {
    console.log("savePreset")
  }

  const testDict = {
    'All' : {
      'Stream1' : {
        'Stream' : {},
        'Volume' : {},
        'Zones' : {},
      },
      'Stream2' : {
        'Stream' : {},
        'Volume' : {},
        'Zones' : {},
      },
      'Stream3' : {
        'Stream' : {},
        'Volume' : {},
        'Zones' : {},
      },
    }
  }
  
  return (
    <Modal onClose={onClose}>
      <Card>
        <div>
          <div className="preset-name">
            Create Preset
          </div>
          <input type="text" value={name} onChange={(e)=>setName(e.target.value)}/>
          <br/>
          <div>
            <IconButton onClick={()=>{savePreset(); onClose()}}> <DoneIcon className="group-button-icon" style={{width:"3rem", height:"3rem"}}/> </IconButton>
          </div>


          <DictToTree dict={testDict}/>
          {/* <FormGroup>
            <FormControlLabel control={<Checkbox defaultChecked />} label="Label" />
          </FormGroup> */}
        </div>
      </Card>
    </Modal>
  )
}

export default CreatePresetModal