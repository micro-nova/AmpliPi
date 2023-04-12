import "./PageHeader.scss";

const PageHeader = ({ title, onClose }) => {
  return (
    <div className="page-header">
      <div className="page-header-close" onClick={onClose}>
        x
      </div>
      <div className="page-header-title">{title}</div>
    </div>
  );
}

export default PageHeader;
