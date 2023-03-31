import './Card.scss'

const Card = ( {children, selected=false} ) => {
    const className = selected ? "card card-selected" : "card"

    return (
        <div className={className}>
            {children}
        </div>
    )
}

export default Card