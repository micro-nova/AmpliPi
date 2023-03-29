import Card from '@/components/Card/Card'
import './PlayerCard.scss'

const PlayerCard = () => {
    return (
        <Card>
            <div className="outer">
                <div className="content">
                    Zones
                </div>
                <div className="content">
                    Stream Name
                </div>
                <div className="content">
                    Image
                </div>
                <div className="content">
                    Description
                </div>
                <div className="content vol">
                    Vol
                </div>
            </div>
        </Card>
    )
}

export default PlayerCard