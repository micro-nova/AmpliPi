import "./ListItem.scss"

const ListItem = ({
  name,
  children,
  onClick = undefined,
  nameFontSize = "2rem",
}) => {
  return (
    <div
      className="list-item-container"
      onClick={onClick != undefined ? onClick : () => {}}
      style={{ cursor: onClick != undefined ? "pointer" : "default" }}
    >
      <div className="list-item-child">{children}</div>
      <div className="list-item-name" style={{ fontSize: nameFontSize }}>
        {name}
      </div>
    </div>
  )
}

export default ListItem
