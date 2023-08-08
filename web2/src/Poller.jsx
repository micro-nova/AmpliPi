import { useStatusStore } from "./App";
import React from "react";
import { useInterval } from "./hooks/useInterval";
import LoadingPage from "./pages/LoadingPage/LoadingPage";

import PropTypes from "prop-types";

const UPDATE_INTERVAL = 1500;

const Poller = ({ children }) => {
    const isLoaded = useStatusStore((s) => s.loaded);
    const disconnected = useStatusStore((s) => s.disconnected);
    const update = useStatusStore((s) => s.fetch);

    // update immediately at start
    React.useEffect(() => {
        update();
    }, []);

    // update periodically
    useInterval(() => {
        update();
    }, UPDATE_INTERVAL);

    if (!isLoaded || disconnected) {
        return <LoadingPage />;
    }
    return children;
};
Poller.propTypes = {
    children: PropTypes.any.isRequired,
};

export default Poller;
