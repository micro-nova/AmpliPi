
import React from "react";
import "./MenuBar.scss";
import BottomNavigation from "@mui/material/BottomNavigation";
import BottomNavigationAction from "@mui/material/BottomNavigationAction";
import HomeIcon from "@mui/icons-material/Home";
import AlbumIcon from "@mui/icons-material/Album";
import SettingsIcon from "@mui/icons-material/Settings";
import QueueMusicIcon from "@mui/icons-material/QueueMusic";
import Badge from "@mui/material/Badge";
import { useStatusStore, usePersistentStore } from "@/App";
import { getSourceInputType } from "@/utils/getSourceInputType";
import { router } from "@/main";

import PropTypes from "prop-types";

const MenuBar = ({ pageNumber }) => {
    const setSelectedPage = (n) => {
        switch (n) {
        default:
            router.navigate("/home");
            break;
        case 1:
            router.navigate("/player");
            break;
        case 2:
            router.navigate("/browser");
            break;
        case 3:
            router.navigate("/settings");
            break;
        }
    };

    const updateAvailable = useStatusStore(
        (s) =>
            s.status.info.version
                .split("+")[0]
                .localeCompare(s.status.info.latest_release, undefined, {
                    numeric: true,
                    sensitivity: "base",
                }) < 0
    );

    const selectedSourceId = usePersistentStore((s) => s.selectedSource);
    const selectedSource = useStatusStore(s => s.status.sources[selectedSourceId]);
    const sourceInputType = getSourceInputType(selectedSource);
    console.log(`sourceInputType MenuBar: ${sourceInputType}`);
    const sourceIsInactive =
    sourceInputType === "none" || sourceInputType == "unknown";
  
    return (
        <div className="bar">
            <BottomNavigation
                value={pageNumber}
                onChange={(event, num) => {
                    setSelectedPage(num);
                }}
            >
                <BottomNavigationAction label="Home" icon={<HomeIcon />} />
                {!sourceIsInactive && (
                    <BottomNavigationAction label="Player" icon={<AlbumIcon />} />
                )}
                {false && (
                    <BottomNavigationAction label="Browser" icon={<QueueMusicIcon />} />
                )}
                <BottomNavigationAction
                    label="Settings"
                    icon={
                        <Badge badgeContent={updateAvailable ? " " : null} color="primary">
                            <SettingsIcon />
                        </Badge>
                    }
                />
            </BottomNavigation>
        </div>
    );
};
MenuBar.propTypes = {
    pageNumber: PropTypes.number.isRequired,
};

export default MenuBar;
