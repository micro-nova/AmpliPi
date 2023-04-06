import './Card.scss'

const Card = ( {children, className, selected=false} ) => {

    return (
        <div className={`card ${className} ${selected ? " card card-selected" : ""}`}>
            {children}
        </div>
    )
}

export default Card