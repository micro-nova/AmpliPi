import React from "react";
import Marquee from "react-fast-marquee";

import PropTypes from "prop-types";

export default function CustomMarquee(props) {
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
                // If the content does not fit the div, and if the scroll is paused, start scrolling after a two second timer
                // The timer is used to create a pause effect, keep the data from simply scrolling infinitely
                scrollPause.current = setTimeout(()=>{setScroll(true)}, 2000);
            } else {
                // if content is not meant to scroll, remove the timer that allows it to start scrolling again
                // This is useful in cases when the screen is resized during a pause phase
                clearTimeout(scrollPause.current);
            }
        }
    }

    let resizeTimeout;  // Your IDE will say this is unused, it's actually used to make sure the timeout below is limited to one instance at a time by taking up a specific variable
    function handleResize(){
        if(!resizeCooldown.current){
            resizeCooldown.current = true;

            assessMarquee()
            resizeTimeout = setTimeout(()=>{resizeCooldown.current = false;}, 1000)
        }
    }
    window.addEventListener("resize", handleResize()); // Doesn't call assessMarquee directly to avoid calling thousands of times per second when resizing window

    React.useEffect(() => {
        setScroll(false);
        assessMarquee();
    }, [children])

    if(marqueeScroll){
        return(
            <Marquee play={marqueeScroll} speed={30} onCycleComplete={() => {setScroll(false); assessMarquee();}}>
            <div
                style={{marginRight: "25px"}} // Uses right margin to provide a gap between the start and end of scroll but without effecting the center align of non-scrolling data
                ref={childrenRef}
            >
                {children}
            </div>
            </Marquee>
        )
    } else {
        return(
            <div
                ref={childrenRef}
            >
                {children}
            </div>
        )
    }
};
CustomMarquee.propTypes = {
    children: PropTypes.string.isRequired,
    containerRef: PropTypes.object.isRequired, // Needs to be a React.useRef specifically, but proptypes doesn't let you specify that
};
