import React from "react";

import "./MenuBar.scss";
import BottomNavigation from "@mui/material/BottomNavigation";
import BottomNavigationAction from "@mui/material/BottomNavigationAction";
import HomeIcon from "@mui/icons-material/Home";
import AlbumIcon from "@mui/icons-material/Album";
import SettingsIcon from "@mui/icons-material/Settings";
import QueueMusicIcon from "@mui/icons-material/QueueMusic";

import PropTypes from "prop-types";



const MenuBar = ({onChange, pageNumber}) => {
    return (
        <div className="bar">
            <BottomNavigation value={pageNumber} onChange={(event, num)=>{onChange(num);}}>
                <BottomNavigationAction label="Home" icon={<HomeIcon/>}/>
                <BottomNavigationAction label="Player" icon={<AlbumIcon/>}/>
                <BottomNavigationAction label="Browser" icon={<QueueMusicIcon/>}/>
                <BottomNavigationAction label="Settings" icon={<SettingsIcon/>}/>
            </BottomNavigation>
        </div>
    );
};
MenuBar.propTypes = {
    onChange: PropTypes.func.isRequired,
    pageNumber: PropTypes.number.isRequired,
};

export default MenuBar;
