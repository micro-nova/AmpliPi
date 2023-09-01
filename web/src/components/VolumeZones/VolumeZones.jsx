import React from "react";
import "./VolumesZones.scss";
import ZoneVolumeSlider from "../ZoneVolumeSlider/ZoneVolumeSlider";
import GroupVolumeSlider from "../GroupVolumeSlider/GroupVolumeSlider";
import Card from "../Card/Card";

import PropTypes from "prop-types";

const VolumeZones = ({ sourceId, open, zones, groups, groupsLeft }) => {
    const groupVolumeSliders = [];
    for (const group of groups) {
        groupVolumeSliders.push(
            <Card className="group-vol-card" key={group.id}>
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
            <Card className="zone-vol-card" key={zone.id}>
                <ZoneVolumeSlider zoneId={zone.id} />
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
};

export default VolumeZones;
