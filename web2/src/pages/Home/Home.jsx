import React from "react";
import PlayerCard from "@/components/PlayerCard/PlayerCard";
import "./Home.scss";
// import { useStatusStore } from "@/App.jsx";

import PropTypes from "prop-types";

export const getSourceZones = (source_id, zones) => {
    let matches = [];
    for (const i of zones) {
        if (i.source_id == source_id) {
            matches.push(i);
        }
    }
    return matches;
};

const Home = ({ selectedSource, setSelectedSource }) => {
    return (
        <div className="home-outer">
            <div className="home-view">
                <PlayerCard
                    sourceId={0}
                    selectedSource={selectedSource}
                    setSelectedSource={setSelectedSource}
                />
                <PlayerCard
                    sourceId={1}
                    selectedSource={selectedSource}
                    setSelectedSource={setSelectedSource}
                />
                <PlayerCard
                    sourceId={2}
                    selectedSource={selectedSource}
                    setSelectedSource={setSelectedSource}
                />
                <PlayerCard
                    sourceId={3}
                    selectedSource={selectedSource}
                    setSelectedSource={setSelectedSource}
                />
            </div>
        </div>

    );
};
Home.propTypes = {
    selectedSource: PropTypes.any.isRequired,
    setSelectedSource: PropTypes.func.isRequired,
};

export default Home;
