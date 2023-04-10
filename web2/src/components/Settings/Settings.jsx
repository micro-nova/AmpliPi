import "./Settings.scss";

import Card from "@/components/Card/Card"

import Modal from '@/components/Modal/Modal'
import Streams from './Streams/Streams'
import Zones from './Zones/Zones'
import Groups from './Groups/Groups'
import Sessions from './Sessions/Sessions'
import Config from './Config/Config'

import { useState } from "react";

const PageListItem = ({name, onClick}) => {

  return (
    <div className="settings-list-item" onClick={onClick}>
      {name}
    </div>
  )

}

const Settings = ({}) => {
  const [openPage, setOpenPage] = useState("")

  const close = () => setOpenPage("")

  let CorePage = ({}) => {
    console.log("changing page to " + openPage)
      switch(openPage) {
        case "Streams":
          return <Streams onClose={close}/>
        case "Zones":
          return <Zones onClose={close}/>
        case "Groups":
          return <Groups onClose={close}/>
        case "Sessions":
          return <Sessions onClose={close}/>
        // case "Configuration and Reset":
        //   return <Config onClose={close}/>
        default:
          return <div></div>
      }
  }
  // wrap in modal if page is open
  // if (openPage !== "") {
  //   Page = () => <Modal onClose={close} className="settings-modal"><div>hi</div></Modal>
  // }

  const Page = () => openPage === "" ? <div /> :
    <Modal onClose={close} className="settings-modal">
      <Card className="settings-card">
        <CorePage />
      </Card>
    </Modal>


  return(
  <div className="settings-outer">
    <div className="settings-header">Settings</div>
    <div className="settings-body">
      <PageListItem name="Streams" onClick={()=>setOpenPage("Streams")}/>
      <PageListItem name="Zones" onClick={()=>setOpenPage("Zones")}/>
      <PageListItem name="Groups" onClick={()=>setOpenPage("Groups")}/>
      <PageListItem name="Sessions" onClick={()=>setOpenPage("Sessions")}/>
      <PageListItem name="Configuration and Reset" onClick={()=>setOpenPage("Configuration and Reset asdf")}/>
      <PageListItem name="Updates" onClick={()=>{window.location.href+='update'}}/>
    </div>
    <Page />
  </div>
  )
}

export default Settings;
