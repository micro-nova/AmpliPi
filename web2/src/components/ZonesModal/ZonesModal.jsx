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
  let usedZones = getSourceZones(sourceId, zones);
  let zonesList = [];
  let selectedZones = [];

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
  

  for (const zone of zones) {
    let selected = false;
    if (zone.source_id == sourceId) {
      selected = true;
      selectedZones.push(zone.id);
    }

    zonesList.push(
      <div
        className="zones-modal-list-item"
        key={zone.id}
      >
        {sourceId != null && (
          <Checkbox
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
          />
        )}
        {zone.name}
      </div>
    );
  }

  return (
    <Modal className="zones-modal">
      <Card className="zones-modal-card">
        <div className="zones-modal-header">Select Zones</div>
        <div className="zones-modal-body">{zonesList}</div>
        <div className="zones-modal-footer">
          <IconButton onClick={()=>{setZones(selectedZones)}}>
            <DoneIcon className="zones-modal-button-icon" style={{width:"3rem", height:"3rem"}}/>
          </IconButton>
        </div>
      </Card>
    </Modal>
  );
};

export default ZonesModal;
