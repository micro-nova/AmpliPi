import "./ZonesModal.scss";
import Modal from "../Modal/Modal";
import Card from "../Card/Card";
import Checkbox from "@mui/material/Checkbox";
import { useState } from "react";
import { IconButton } from "@mui/material";
import DoneIcon from '@mui/icons-material/Done';
import { width } from "@mui/system";
import { useStatusStore } from "@/App.jsx";
import { getSourceZones } from "@/pages/Home/Home";

const ZonesModal = ({ sourceId, setZoneModalOpen }) => {
  const zones = useStatusStore.getState().status.zones
  const groups = useStatusStore.getState().status.groups
  let usedZones = [];
  let usedGroups = [];
  let listItems = [];
  let selectedZones = [];
  let selectedGroups = [];

  const ZonesModalZoneItem = ({ zone, selectable, selected }) => {

    return(
    <div
      className="zones-modal-list-item"
      key={zone.id}
    >
        {selectable && <Checkbox
          onChange={(event) => {
            if (event.target.checked) {
              selectedZones.push(zone.id);
            } else {
              const index = selectedZones.indexOf(zone.id);
              if (index > -1) {
                selectedZones.splice(index, 1);
              }
            }
          }}
          defaultChecked={selected}
        />}
      {zone.name}
    </div>
    )
  }

  const ZonesModalGroupItem = ({ group, selectable, selected }) => {
    return(
      <div
        className="zones-modal-list-item"
        key={group.id}
      >
          {selectable && <Checkbox
            onChange={(event) => {
              if (event.target.checked) {
                selectedGroups.push(group.id);
              } else {
                const index = selectedGroups.indexOf(group.id);
                if (index > -1) {
                  selectedGroups.splice(index, 1);
                }
              }
            }}
            defaultChecked={selected}
          />}
        {group.name}
      </div>
      )
  }

  const setZones = (zoneIds) => {
    let removeList = []

    for(const zone of usedZones){
      if(!zoneIds.includes(zone.id)){
        removeList.push(zone.id)
      }
    }

    fetch(`/api/zones`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({ zones: removeList, update:{source_id:-1} }),
    });

    fetch(`/api/zones`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({ zones: zoneIds, update:{mute: false, source_id:sourceId} }),
    });

    setZoneModalOpen(false)
  }

  const setGroups = (groupIds) => {
    let removeList = []

    for(const group of usedGroups){
      if(!groupIds.includes(group.id)){
        removeList.push(group.id)
      }
    }

    for (const i of removeList) {
      fetch(`/api/groups/${i}`, {
        method: "PATCH",
        headers: {
          "Content-type": "application/json",
        },
        body: JSON.stringify({ source_id: -1 }),
      });
    }

    for (const i of groupIds) {
      fetch(`/api/groups/${i}`, {
        method: "PATCH",
        headers: {
          "Content-type": "application/json",
        },
        body: JSON.stringify({ source_id: sourceId, mute: false }),
      });
    }
  }

  for (const zone of zones) {
    let selected = false;
    if (zone.source_id == sourceId) {
      selected = true;
      selectedZones.push(zone.id);
      usedZones.push(zone)
    }

    listItems.push(
      ZonesModalZoneItem({ zone: zone, selectable: true, selected: selected })
    )
  }

  for (const group of groups) {
    let selected = false;
    if (group.source_id == sourceId) {
      selected = true;
      selectedGroups.push(group.id);
      usedGroups.push(group)
    }
    listItems.push(
      ZonesModalGroupItem({ group: group, selectable: true, selected: selected })
    )
    }

  return (
    <Modal className="zones-modal">
      <Card className="zones-modal-card">
        <div className="zones-modal-header">Select Zones</div>
        <div className="zones-modal-body">{listItems}</div>
        <div className="zones-modal-footer">
          <IconButton onClick={()=>{setZones(selectedZones); setGroups(selectedGroups)}}>
            <DoneIcon className="zones-modal-button-icon" style={{width:"3rem", height:"3rem"}}/>
          </IconButton>
        </div>
      </Card>
    </Modal>
  );
};

export default ZonesModal;
