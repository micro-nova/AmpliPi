import { useState } from "react"
import { useEffect } from "react"
import { useStatusStore } from "@/App"
import Modal from '@/components/Modal/Modal'
import Card from '@/components/Card/Card'
import DoneIcon from '@mui/icons-material/Done'
import './CreatePresetModal.scss'

import Checkbox from '@mui/material/Checkbox';
import IconButton from '@mui/material/IconButton';
import FormControlLabel from '@mui/material/FormControlLabel';
import Box from '@mui/material/Box';

const baseDict = (open, name, content) => {
  return {
    'open' : open,
    'checked' : false,
    'name' : name,
    'content' : content
  }
}

const dictWithOptions = (name) => {
  return baseDict(false, name, [
    baseDict(false, 'Stream', []),
    baseDict(false, 'Volume', []),
    baseDict(false, 'Zones', []),
  ])
}

const buildTreeDict = (status) => {
  const statusClone = JSON.parse(JSON.stringify(status))

  const sourceDicts = statusClone.sources.filter(source => source.info.state !== 'stopped').map(source => dictWithOptions(source.info.name));

  const top = baseDict(false, "All", sourceDicts)
  return top;
}

const isEmpty = (dict) => Object.keys(dict).length === 0

const DictToTree = ({dict, depth=0}) => {
  if (isEmpty(dict)) return <div />
  let entries = []
  let i = 0
  for (const [key, value] of Object.entries(dict)) {

    entries.push(
      <>
        <Box key={i} sx={{ display: 'flex', flexDirection: 'column', ml: 3*depth }}>
          <FormControlLabel
          label={key}
          control={<Checkbox checked={0}/>}
          />
          <DictToTree dict={value} depth={depth+1} />
        </Box>
      </>
    )

    i += 1
  }

  return entries
}

const Structured2Child = ({checked, setChecked, level, setLevel, index}) => {
  const myChecked = checked[index]
  const myLevel = level[index]

}

const getTotalCheckboxes = (d) => d.content.reduce((partialSum, d2) => partialSum + getTotalCheckboxes(d2), 1)

const Structured2Top = ({dict}) => {
  // this function uses a flat representation of the tree structure.
  // each child will get the state getters/setters along with their index within the state
  const totalCheckboxes = getTotalCheckboxes(dict)
  const [checked, setChecked] = useState(Array(totalCheckboxes).fill('unchecked'))
  const [level, setLevel] = useState(Array(totalCheckboxes).fill(0))
}

const StructuredDictAsTree = ({dict, depth=0, checkedInit=false, passInSetCheckedRecur=null, passInGetCheckedRecur=null, refreshTop=null}) => {
  const [checked, setChecked] = useState(checkedInit)

  const setCheckedEffect = (s) => {

  }

  let childSetChecked = []
  let childGetChecked = []

  const setParentChildSetChecked = (setter) => {
    childSetChecked.push(setter)
  }
  const setParentChildGetChecked = (getter) => {
    childGetChecked.push(getter)
  }
  
  const calculateInd = () => {
    if (childGetChecked.length > 0) {
      let s = childGetChecked.reduce((acc, curr) => curr() === 'ind' ? 'ind' : (acc === curr() ? acc : 'ind'), childGetChecked[0]())
      // TODO: can i do setChecked here?
      setChecked(s)
      
      return s
    }

    return checked
  }

  if (refreshTop === null) {
    refreshTop = () => {
      calculateInd()
    }
  }

  const handlePress = (e) => {
    const newChecked = e.target.checked ? 'checked' : 'unchecked'
    
    if (childSetChecked !== null) {
      
      // childSetChecked.forEach(it => it(e.target.checked ? 'checked' : 'unchecked'))
      childSetChecked.forEach(it => it(newChecked))
      // childSetChecked()
    }
    setChecked(e.target.checked ? 'checked' : 'unchecked')
    refreshTop()
  }

  let entries = []
  let i = 0

  for (const d of dict.content) {
    entries.push(
      <StructuredDictAsTree key={i} dict={d} depth={depth+1} checkedInit={checked} passInSetCheckedRecur={setParentChildSetChecked} passInGetCheckedRecur={setParentChildGetChecked} refreshTop={refreshTop}/>
    )
    i += 1
  }

  if (passInSetCheckedRecur !== null) {
    passInSetCheckedRecur((s) => {setChecked(s); childSetChecked.forEach(it => it(s))})
  }
  if (passInGetCheckedRecur !== null) {
    if (childGetChecked.length > 0) {
      passInGetCheckedRecur(calculateInd)
    } else {
      passInGetCheckedRecur(() => checked) // TODO: maybe this is being captured by value, might need to wrap in array
    }
  }

  
  return (
    <>
      <Box sx={{ display: 'flex', flexDirection: 'column', ml: 3*depth }}>
        <FormControlLabel
        label={dict.name}
        control={<Checkbox checked={checked === 'checked'} indeterminate={checked === 'ind'} onChange={handlePress} onMouseLeave={refreshTop()}/>}
        />
        {/* <DictToTree dict={value} depth={depth+1} /> */}
        {entries}
      </Box>
    </>
  )
}

const CreatePresetModal = ({ onClose }) => {
  const [name, setName] = useState('name')

  const status = useStatusStore(s => s.status)

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

  const structuredDict = buildTreeDict(status)

  
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


          {/* <DictToTree dict={testDict}/> */}
          <StructuredDictAsTree dict={structuredDict} checkedInit={'unchecked'}/>
        </div>
      </Card>
    </Modal>
  )
}

export default CreatePresetModal