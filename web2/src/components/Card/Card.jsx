import "./Card.scss"

const Card = ({ backgroundImage=null, children, className='', selected = false }) => {
  const cName = `card ${className} ${selected ? "card-selected" : ""}`

  if (backgroundImage !== null) {
    return (
      <div className={cName} style={{
        background: `linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url('${backgroundImage}')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        }}>
        {children}
      </div>
    )
  }
  return (
    <div className={cName}>
      {children}
    </div>
  )
}

export default Card
