import React from "react";
import "./VolumesZones.scss";
import { useStatusStore } from "@/App.jsx";
import { getSourceZones } from "@/pages/Home/Home";
import ZoneVolumeSlider from "../ZoneVolumeSlider/ZoneVolumeSlider";
import GroupVolumeSlider from "../GroupVolumeSlider/GroupVolumeSlider";
import Card from "../Card/Card";

import { getFittestRep } from "@/utils/GroupZoneFiltering";

import PropTypes from "prop-types";

const VolumeZones = ({ sourceId }) => {
    const zones = getSourceZones(
        sourceId,
        useStatusStore((s) => s.status.zones)
    );
    const groups = getSourceZones(
        sourceId,
        useStatusStore((s) => s.status.groups)
    );

    // compute the best representation of the zones and groups
    const { zones: zonesLeft, groups: usedGroups } = getFittestRep(zones, groups);

    const groupsLeft = groups.filter(
        (g) => !usedGroups.map((ug) => ug.id).includes(g.id)
    );

    const groupVolumeSliders = [];
    for (const group of usedGroups) {
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
    zonesLeft.forEach((zone) => {
        zoneVolumeSliders.push(
            <Card className="zone-vol-card" key={zone.id}>
                <ZoneVolumeSlider zoneId={zone.id} />
            </Card>
        );
    });

    return (
        <div className="volume-sliders-container">
            {groupVolumeSliders}
            {zoneVolumeSliders}
        </div>
    );
};
VolumeZones.propTypes = {
    sourceId: PropTypes.any.isRequired,
};

export default VolumeZones;
