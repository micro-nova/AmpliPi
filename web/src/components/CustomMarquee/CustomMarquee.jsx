import React from "react";
import Marquee from "react-fast-marquee";

import PropTypes from "prop-types";

function CustomMarquee(props) {
    const {
        children,
        containerRef,
    } = props;
    const resizeCooldown = React.useRef(false);

    const childrenRef = React.useRef(null);
    const [childrenScroll, setChildScroll] = React.useState(false);
    const childrenOverrideTimeout = React.useRef(null);
    const childrenScrollOverride = React.useRef(true); // set to true by defualt so that there is no scrolling on load, until a setTimeout later on changes that 2 seconds after load

    React.useEffect(() => {assessMarquee();}, [children]);

    function assessMarquee() {
        const container = containerRef.current;
        const scroll = childrenRef.current;

        if(container && scroll){
            if(container.offsetWidth < scroll.scrollWidth && !childrenScrollOverride.current){
                setChildScroll(true);
            } else if(container.offsetWidth >= scroll.scrollWidth && childrenScrollOverride.current){
                clearTimeout(childrenOverrideTimeout.current);
            }
        }
    }

    function setOverride(){
        setChildScroll(false);
        childrenScrollOverride.current = true;

        childrenOverrideTimeout.current = setTimeout(()=>{childrenScrollOverride.current = false; assessMarquee();}, 2000); // When a scroll completes, pause for two seconds and restart (unless the timeout is cleared)
    }

    setTimeout(()=>{childrenScrollOverride.current = false; assessMarquee();}, 2000) // used to kick off useEffect after two seconds of page load


    function handleResize(){
        if(!resizeCooldown.current){
            resizeCooldown.current = true;

            assessMarquee()

            setTimeout(()=>{resizeCooldown.current = false;}, 1000) // set a cooldown for resize checks to avoid excessive renders
        }
    }
    window.addEventListener("resize", handleResize()); // Doesn't call assessMarquee directly to avoid calling thousands of times per second when resizing window


    return(
        <Marquee play={childrenScroll} speed={30} onCycleComplete={() => {setOverride()}}>
            <div
                style={{marginLeft: "10px"}} //Needs inline styling for margin to add a gap between start and end of marquee, also keeps marquee from "overscrolling" (stopping a pixel or two after reaching the wraparound point due to minor lag)
                className="marquee-text"
                ref={childrenRef}
            >
                {children}
            </div>
        </Marquee>
    )
};
CustomMarquee.propTypes = {
    children: PropTypes.string.isRequired,
    containerRef: PropTypes.object.isRequired, // Needs to be a React.useRef specifically, but proptypes doesn't let you specify that
};

export default CustomMarquee;
