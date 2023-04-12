import './Zones.scss'
import { useStatusStore } from '@/App.jsx'
import { useState } from 'react'
import PageHeader from '@/components/PageHeader/PageHeader'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { Button, TextField } from '@mui/material';

//TODO: styling

const ZoneListItem = ({ zone }) => {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState(zone.name)
  const [vol_max, setVolMax] = useState(zone.vol_max)
  const [vol_min, setVolMin] = useState(zone.vol_min)
  const [disabled, setDisabled] = useState(zone.disabled)

  const applyChanges = () => {
    console.log("Applying changes to zone", zone.id)
    console.log("Name:", name)
    console.log("Max Volume:", vol_max)
    console.log("Min Volume:", vol_min)
    console.log("Disabled:", disabled)
    fetch(`/api/zones/${zone.id}`,
    {
      method: 'PATCH',
      headers : { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({name: name, vol_max: vol_max, vol_min: vol_min, disabled: disabled})
    })
  }

  return (
    <div className='zones-zone-column'>
      <div className='zones-zone-row'>
        <div className='zones-zone-name'>
          {zone.name}
        </div>
        {
          open ? <KeyboardArrowUpIcon className='zones-zone-expand-button' style={{width:"3rem", height:"3rem"}} onClick={() => setOpen(!open)}/> :
          <KeyboardArrowDownIcon className='zones-zone-expand-button' style={{width:"3rem", height:"3rem"}} onClick={() => setOpen(!open)}/>
        }
      </div>
      {open &&
        <div>
          <div>
            Name:
            <input type="text" name="Name" value={name} onChange={(e)=>{setName(e.target.value)}}/>
          </div>
          <div>
            Max Volume:
            <input type="text" name="Max Volume" value={vol_max} onChange={(e)=>{setVolMax(e.target.value)}}/>
          </div>
          <div>
            Min Volume:
            <input type="text" name="Min Volume" value={vol_min} onChange={(e)=>{setVolMin(e.target.value)}}/>
          </div>
          <div>
            Disabled:
            <input type="checkbox" name="Disabled" checked={disabled} onChange={(e)=>{setDisabled(e.target.checked)}}/>
          </div>
          <div>
            <Button variant="contained" onClick={applyChanges}>Apply</Button>
          </div>
        </div>
      }
    </div>
  )

}


const Zones = ({ onClose }) => {
  const zones = useStatusStore((state) => state.status.zones)

  const listItems = zones.map((zone) => {
    return (
      <ZoneListItem zone={zone} key={zone.id} />
    )
  })

  return (<>
      <PageHeader title="Zones" onClose={onClose} />
      <div className="zones-body">
        {listItems}
      </div>
  </>)
}

export default Zones
