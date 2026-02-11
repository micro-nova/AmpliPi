import React from "react";
import "./VolumesZones.scss";
import ZoneVolumeSlider from "../ZoneVolumeSlider/ZoneVolumeSlider";
import GroupVolumeSlider from "../GroupVolumeSlider/GroupVolumeSlider";
import Card from "../Card/Card";
import RectangularButton from "@/components/RectangularButton/RectangularButton";

import PropTypes from "prop-types";

const VolumeZones = ({ sourceId, open, zones, groups, groupsLeft, setZonesModalOpen }) => {
    const groupVolumeSliders = [];
    for (const group of groups) {
        groupVolumeSliders.push(
            <Card secondary className="group-vol-card vol-margin" key={group.id}>
                <GroupVolumeSlider
                    groupId={group.id}
                    sourceId={sourceId}
                    groupsLeft={groupsLeft}
                />
            </Card>
        );
    }

    const zoneVolumeSliders = [];
    zones.forEach((zone) => {
        zoneVolumeSliders.push(
            <Card secondary className="zone-vol-card vol-margin" key={zone.id}>
                <ZoneVolumeSlider zoneId={zone.id} />
            </Card>
        );
    });

    const noZones = zoneVolumeSliders.length == 0 && groupVolumeSliders.length == 0;

    if (open) {
        return (
            <div className={`volume-sliders-container ${(!noZones) && "add-padding"}`}>
                {groupVolumeSliders}
                {zoneVolumeSliders}
                <RectangularButton large label="+" onClick={() => {setZonesModalOpen(true);}} />
            </div>
        );
    } else if (noZones){
        return(
            <div className="volume-sliders-container">
                <RectangularButton large label="+" onClick={() => {setZonesModalOpen(true);}} />
            </div>
        );
    }
};
VolumeZones.propTypes = {
    sourceId: PropTypes.any.isRequired,
    open: PropTypes.bool.isRequired,
    zones: PropTypes.array.isRequired,
    groups: PropTypes.array.isRequired,
    groupsLeft: PropTypes.array.isRequired,
    setZonesModalOpen: PropTypes.func.isRequired,
};

export default VolumeZones;
