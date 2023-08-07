import React from "react";
import "./GroupVolumeSlider.scss";
import { getSourceZones } from "@/pages/Home/Home";
import { useStatusStore } from "@/App";
import ZoneVolumeSlider from "../ZoneVolumeSlider/ZoneVolumeSlider";
import { IconButton } from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import VolumeSlider from "../VolumeSlider/VolumeSlider";
import { getFittestRep } from "@/utils/GroupZoneFiltering";

import PropTypes from "prop-types";

let sendingRequestCount = 0;

// volume slider for a group in the volumes drawer
const GroupVolumeSlider = ({ groupId, sourceId, groupsLeft }) => {
    const group = useStatusStore(s => s.status.groups.filter(g => g.id === groupId)[0]);
    const volume = group.vol_f;
    const setGroupVol = useStatusStore(s => s.setGroupVol);
    const setGroupMute = useStatusStore(s => s.setGroupMute);
    const [slidersOpen, setSlidersOpen] = React.useState(false);


    // get zones for this group
    const groupZones = getSourceZones(sourceId, useStatusStore(s => s.status.zones)).filter(z => group.zones.includes(z.id));

    // pull out subgroups
    const {zones: zonesLeft, groups: subgroups} = getFittestRep(groupZones, groupsLeft);
    const newGroupsLeft = groupsLeft.filter(g => !subgroups.map(sg => sg.id).includes(g.id));

    const zonesLeftIds = zonesLeft.map(z => z.id);
    const subgroupIds = subgroups.map(g => g.id);

    const zoneSliders = [];
    for (const zoneId of zonesLeftIds) {
        zoneSliders.push(<ZoneVolumeSlider key={zoneId} zoneId={zoneId} />);
    }

    const subgroupItems = [];
    for (const subgroupId of subgroupIds) {
        subgroupItems.push(<GroupVolumeSlider key={subgroupId} groupId={subgroupId} sourceId={sourceId} groupsLeft={newGroupsLeft} />);
    }

    const setVol = (vol, force = false) => {
        setGroupVol(groupId, vol);

        if (sendingRequestCount <= 0 || force) {
            sendingRequestCount += 1;
            fetch(`/api/groups/${groupId}`, {
                method: "PATCH",
                headers: {
                    "Content-type": "application/json",
                },
                body: JSON.stringify({ vol_f: vol, mute: false }),
            }).then(() => {
                sendingRequestCount -= 1;
            });
        }
    };

    const setMute = (mute) => {
        setGroupMute(groupId, mute);

        fetch(`/api/groups/${groupId}`, {
            method: "PATCH",
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({ mute: mute }),
        });
    };

    return (
        <div className="group-volume-container">
            {group.name[0].toUpperCase() + group.name.slice(1)}
            <div className="group-zones-container">
                <div className="group-volume-slider">
                    <VolumeSlider
                        mute={group.mute}
                        setMute={setMute}
                        vol={volume}
                        setVol={setVol}
                    />
                </div>

                <IconButton
                    style={{ padding: "0px" }}
                    onClick={() => setSlidersOpen(!slidersOpen)}
                >
                    {slidersOpen ? (
                        <KeyboardArrowUpIcon
                            className="group-slider-expand-button"
                            style={{ width: "3rem", height: "3rem" }}
                        />
                    ) : (
                        <KeyboardArrowDownIcon
                            className="group-slider-expand-button"
                            style={{ width: "3rem", height: "3rem" }}
                        />
                    )}
                </IconButton>
            </div>
            {slidersOpen && subgroupItems.length > 0 && (
                <div className="group-volume-children-container">{subgroupItems}</div>
            )}
            {slidersOpen && (
                <div className="group-volume-children-container">{zoneSliders}</div>
            )}
        </div>
    );
};
GroupVolumeSlider.propTypes = {
    groupId: PropTypes.any.isRequired,
    sourceId: PropTypes.any.isRequired,
    groupsLeft: PropTypes.any.isRequired,
};

export default GroupVolumeSlider;
