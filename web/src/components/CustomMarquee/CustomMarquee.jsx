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
    const [marqueeScroll, setScroll] = React.useState(false);
    const scrollPause = React.useRef(null);

    function assessMarquee() {
        // This function is called in two cases:
        // 1. a marquee scroll cycle has completed
        // 2. the screen was resized
        const container = containerRef.current;
        const scroll = childrenRef.current;

        if(container && scroll){ // Only start checking after pageload

            // This if statement is watching two states:
            // 1. The screen size (more specifically, the size of the text vs size of the div it's inside of)
            // 2. A boolean
            //
            // The screen size is set based on the device using the UI and/or the browser window size
            // The boolean is set to true by the timer within the if statement, and set to false whenever a marquee scroll cycle completes

            if(container.offsetWidth < scroll.scrollWidth && !marqueeScroll){
                // If the content does not fit the div, and if the scroll is not paused, start scrolling after a two second timer
                // The timer is used to create a pause effect, keep the data from simply scrolling infinitely
                scrollPause.current = setTimeout(()=>{setScroll(true)}, 2000);
            } else {
                // if content is not meant to scroll, remove the timer that allows it to start scrolling again
                // This is useful in cases when the screen is resized or the song changes during a pause phase
                clearTimeout(scrollPause.current);
            }
        }
    }

    setTimeout(()=>{assessMarquee();}, 2000) // used to kick off useEffect after two seconds of page load


    function handleResize(){
        if(!resizeCooldown.current){
            resizeCooldown.current = true;

            assessMarquee()

            setTimeout(()=>{resizeCooldown.current = false;}, 1000) // set a cooldown for resize checks to avoid excessive renders
        }
    }
    window.addEventListener("resize", handleResize()); // Doesn't call assessMarquee directly to avoid calling thousands of times per second when resizing window


    return(
        <Marquee play={marqueeScroll} speed={30} onCycleComplete={() => {setScroll(false); assessMarquee();}}>
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
