import React from "react";
import "./VolumesZones.scss";
import ZoneVolumeSlider from "../ZoneVolumeSlider/ZoneVolumeSlider";
import GroupVolumeSlider from "../GroupVolumeSlider/GroupVolumeSlider";
import Card from "../Card/Card";

import PropTypes from "prop-types";

const VolumeZones = ({ sourceId, open, zones, groups, groupsLeft, alone }) => {
    const groupVolumeSliders = [];
    for (const group of groups) {
        groupVolumeSliders.push(
            <Card secondary={!alone} className={`group-vol-card ${!alone ? "vol-margin" : ""}`} key={group.id}>
                <GroupVolumeSlider
                    alone={alone}
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
            <Card secondary={!alone} className={`zone-vol-card ${!alone ? "vol-margin" : ""}`} key={zone.id}>
                <ZoneVolumeSlider alone={alone} zoneId={zone.id} />
            </Card>
        );
    });

    if(open){
        return (
            <div className="volume-sliders-container">
                {groupVolumeSliders}
                {zoneVolumeSliders}
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
    alone: PropTypes.bool,
};
VolumeZones.defaultProps = {
    alone: false,
}

export default VolumeZones;
