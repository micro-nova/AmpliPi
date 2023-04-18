import "./MenuBar.scss";
import BottomNavigation from "@mui/material/BottomNavigation";
import BottomNavigationAction from "@mui/material/BottomNavigationAction";
import HomeIcon from '@mui/icons-material/Home';
import AlbumIcon from '@mui/icons-material/Album';
import SettingsIcon from '@mui/icons-material/Settings';
import QueueMusicIcon from '@mui/icons-material/QueueMusic';
import Badge from "@mui/material/Badge";
import { useStatusStore } from "@/App";



const MenuBar = ({onChange, pageNumber}) => {

  const updateAvailable = useStatusStore((s) => s.status.info.latest_release > s.status.info.version.split('+')[0])

  return (
    <div className="bar">
      <BottomNavigation value={pageNumber} onChange={(event, num)=>{onChange(num)}}>
        <BottomNavigationAction label="Home" icon={<HomeIcon/>}/>
        <BottomNavigationAction label="Player" icon={<AlbumIcon/>}/>
        <BottomNavigationAction label="Browser" icon={<QueueMusicIcon/>}/>
        <BottomNavigationAction label="Settings" icon={<Badge badgeContent={ updateAvailable ? ' ' : null} color="primary"><SettingsIcon/></Badge>}/>
      </BottomNavigation>
    </div>
  );
};

export default MenuBar;
