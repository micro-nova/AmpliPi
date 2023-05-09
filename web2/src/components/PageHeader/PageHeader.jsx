import "./PageHeader.scss"
import CloseIcon from '@mui/icons-material/Close';


const PageHeader = ({ title, onClose }) => {
  return (
    <div className="page-header">
      <div className="page-header-title">{title}</div>
      <div className="page-header-close" onClick={onClose}>
        <CloseIcon fontSize="inherit"></CloseIcon>
      </div>
    </div>
  )
}

export default PageHeader
