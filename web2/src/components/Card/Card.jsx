import "./Card.scss"

// card is a custom container with rounded corners.
// backgroundImage can be assigned, which is used for PlayerCardFb
const Card = ({
  backgroundImage = null,
  children,
  className = "",
  selected = false,
  onClick = null,
}) => {
  const cName = `card ${className} ${selected ? "selected" : ""}`
  const onClickFun = onClick === null ? () => {} : onClick
  const topTransparency = selected ? 0.25 : 0.4
  const bottomTransparency = selected ? 0.25 : 0.9

  const backgroundSize =
    backgroundImage !== null && backgroundImage.includes("static/imgs/")
      ? "contain"
      : "cover"

  if (backgroundImage !== null) {
    return (
      <div
        className={cName}
        onClick={onClickFun}
        style={{
          backgroundImage: `linear-gradient(rgba(0, 0, 0, ${topTransparency}), rgba(0, 0, 0, ${bottomTransparency})), url('${backgroundImage}')`,
          backgroundSize: `${backgroundSize}`,
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
        }}
      >
        {children}
      </div>
    )
  }
  return <div className={cName}>{children}</div>
}

export default Card
