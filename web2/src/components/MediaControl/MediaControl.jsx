import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faStepBackward } from '@fortawesome/free-solid-svg-icons'
import { faStepForward } from '@fortawesome/free-solid-svg-icons'
import { faPause } from '@fortawesome/free-solid-svg-icons'
import { faPlay } from '@fortawesome/free-solid-svg-icons'
import { faStop } from '@fortawesome/free-solid-svg-icons'

import './MediaControl.scss'

const MediaControl = ({ source }) => {
    const sources = status.sources;
    console.log("hhhhhi")
    const playing = source.info.state.includes('playing') 

    const isSupported = (cmd) => { return source.info.supported_cmds.includes(cmd) }
    
    const Center = (() => {
        if (playing) {
            if (isSupported('pause')) {
                return <FontAwesomeIcon icon={faPause} className="media-control" />
            } else if (isSupported('stop')) {
                return <FontAwesomeIcon icon={faStop} className="media-control" /> 
            } else {
                return <FontAwesomeIcon icon={faPause} className="media-control media-control-disabled" />
            }
        } else {
            if (isSupported('play')) {
                return <FontAwesomeIcon icon={faPlay} className="media-control" /> 
            } else {
                return <FontAwesomeIcon icon={faPlay} className="media-control media-control-disabled" /> 
            }
        }
    })()

    const cmdToClassName = (cmd) => { return isSupported(cmd) ? "media-control" : "media-control media-control-disabled" }


    const Backward = <FontAwesomeIcon icon={faStepBackward} className={cmdToClassName('prev')} />
    const Forward = <FontAwesomeIcon icon={faStepForward} className={cmdToClassName('next')} />



    return (
        <div className="media-outer">
            <div className="media-inner">
                {Backward}
                {Center}
                {Forward}
            </div>
        </div>
    )
}

export default MediaControl