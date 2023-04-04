import "./ZonesModal.scss";
import Modal from "../Modal/Modal";
import Card from "../Card/Card";
import Checkbox from "@mui/material/Checkbox";
import { useState } from "react";
import { IconButton } from "@mui/material";
import DoneIcon from '@mui/icons-material/Done';
import { width } from "@mui/system";

const ZoneItem => () {

}

const GroupItem => () {

}

const ZonesModal = ({ groups, zones, sourceId, setZones }) => {
  let zonesList = [];
  let selectedZones = [];
  let selectedGroups = [];

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
          <IconButton onClick={()=>{setZones(selectedZones, selectedGroups)}}>
            <DoneIcon className="zones-modal-button-icon" style={{width:"3rem", height:"3rem"}}/>
          </IconButton>
        </div>
      </Card>
    </Modal>
  );
};

export default ZonesModal;
