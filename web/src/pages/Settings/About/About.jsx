import React from "react";
import PageHeader from "@/components/PageHeader/PageHeader";
import { useStatusStore } from "@/App";
import "./About.scss";

import PropTypes from "prop-types";

const About = ({ onClose }) => {
    const info = useStatusStore.getState().status.info;

    const generateBoardVersionsString = (fw) => {
		let temp_string = fw[1].version;
        for(let i = 2; i < fw.length; i++) {
			temp_string += ", ";
        	temp_string += fw[i].version;
        }
        return temp_string
    }
    
    return (
        <>
            <PageHeader title="About" onClose={onClose} />
            <div className="about-body">
                <a className="link" href="http://www.amplipi.com">
          Amplipi ™
                </a>
                <br />
        by{" "}
                <a className="link" href="http://www.micro-nova.com">
          MicroNova
                </a>{" "}
        © {new Date(Date.now()).getFullYear()}
                <br />
        Version: {info.version}
                <br />
        {!info.is_streamer && ( <>
        Main Unit Firmware Version: {info.fw.length ? info.fw[0].version: "No Preamp"} 
                <br />
        </> ) }
        {info.fw.length > 1 && ( <>
        Expansion Unit Firmware Version{info.fw.length > 2? "s": ""}: {generateBoardVersionsString(info.fw)}
                <br />
        </> ) }               
        Latest: {info.latest_release}
                <br />
        {info.access_key && ( <>
        Access key: {info.access_key}
                <br />
        </> ) }
                <div className="about-links">
          Links:
                    <a className="link" href="/doc">
            Browsable API
                    </a>
                    <a className="link" href="https://github.com/micro-nova/AmpliPi">
            Github
                    </a>
                    <a className="link" href="https://amplipi.discourse.group/">
            Community
                    </a>
                    <a
                        className="link"
                        href="https://github.com/micro-nova/AmpliPi/blob/main/COPYING"
                    >
            License
                    </a>
                    <a
                        href={window.location.href}
                        onClick={() => {
                            window.location.href =
                "http://" + window.location.hostname + ":19531/entries";
                        }}
                    >
            Logs
                    </a>
                </div>
            </div>
        </>
    );
};
About.propTypes = {
    onClose: PropTypes.func.isRequired,
};

export default About;
