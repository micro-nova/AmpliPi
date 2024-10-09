import { useStatusStore } from "./App";
import React from "react";
import { useInterval } from "./hooks/useInterval";
import LoadingPage from "./pages/LoadingPage/LoadingPage";

import PropTypes from "prop-types";

const UPDATE_INTERVAL = 1500;

const Poller = ({ children }) => {
    const isLoaded = useStatusStore((s) => s.loaded);
    const disconnected = useStatusStore((s) => s.disconnected);
    const getSystemState = useStatusStore((s) => s.getSystemState);

    // update immediately at start
    React.useEffect(() => {
        getSystemState();
    }, []);

    // update periodically
    useInterval(() => {
        getSystemState();
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
