import { create } from 'zustand'
import { useState, useEffect } from 'react'
import { useStatusStore } from "@/App"
import produce from 'immer'

import Modal from '@/components/Modal/Modal'
import Card from '@/components/Card/Card'
import DoneIcon from '@mui/icons-material/Done'
import './CreatePresetModal.scss'

import Checkbox from '@mui/material/Checkbox';
import IconButton from '@mui/material/IconButton';
import FormControlLabel from '@mui/material/FormControlLabel';
import Box from '@mui/material/Box';

const setCheckedRecur = (dict, checked) => {dict.checked = checked; dict.content.forEach(it => setCheckedRecur(it, checked))}

const computeCheckedStateRecur = (dict) => {
  if (dict.content.length === 0) {
    return dict.checked
  }

  let c = computeCheckedStateRecur(dict.content[0])
  for (let i = 1; i < dict.content.length; i++) {
    let curr = computeCheckedStateRecur(dict.content[i])
    if (c === 'ind' || curr === 'ind' || c !== curr) {
      c = 'ind'
    }
  }

  // let newCheckedState = dict.content.reduce((acc, curr) => (
  //   computeCheckedStateRecur(curr) === 'ind' ? 'ind' : // if ind, keep ind
  //   (acc === computeCheckedStateRecur(curr) ? acc : 'ind'), // if same, keep same. else ind
  //   computeCheckedStateRecur(dict.content[0])) // init value
  //   )
    dict.checked = c
    return c
}

const useTreeStore = create((set) => ({
  tree: null,
  setTree: (newTree) => {
    set({tree: newTree})
  },
  setChecked: (path, checked) => {
    set(produce((s) => {
      // navigate to desired tree
      console.log("logging path.....")
      console.log(path)
      console.log("path logged bruh")
      let curr = s.tree
      for (const p of path) {
        console.log(curr.content.length)
        curr = curr.content[p]
      }
      // set checked on tree and all children recursively
      setCheckedRecur(curr, checked)

      // recompute checked state
      computeCheckedStateRecur(s.tree)
    }))
  }
}))

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

const StructuredDictAsTree = ({dict, depth=0, path=[]}) => {
  const setChecked = useTreeStore((s) => s.setChecked)
  const checked = dict.checked

  const handlePress = (e) => {
    setChecked(path, e.target.checked ? 'checked' : 'unchecked')
  }

  let entries = []
  let i = 0
  for (const d of dict.content) {
    entries.push(
      <StructuredDictAsTree key={i} dict={d} depth={depth+1} path={[...path, i]}/>
    )
    i += 1
  }

  return (
    <>
      <Box sx={{ display: 'flex', flexDirection: 'column', ml: 3*depth }}>
        <FormControlLabel
        label={dict.name}
        control={<Checkbox checked={checked === 'checked'} indeterminate={checked === 'ind'} onChange={handlePress}/>}
        />
        {entries}
      </Box>
    </>
  )
}

const CreatePresetModal = ({ onClose }) => {
  const [name, setName] = useState('name')
  const status = useStatusStore(s => s.status)
  const setTree = useTreeStore(s => s.setTree)
  const tree = useTreeStore(s => s.tree)

  console.log("setting tree...")
  useEffect(() => {
    const newTree = buildTreeDict(status)
    console.log("new tree")
    console.log(newTree)
    setTree(newTree)
  }, [])
  

  const savePreset = () => {
    console.log("savePreset")
  }

  if (tree === null) return <div/>

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
          <StructuredDictAsTree dict={tree}/>
        </div>
      </Card>
    </Modal>
  )
}

export default CreatePresetModal