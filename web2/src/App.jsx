import { useEffect, useState } from "react";
import "@/App.scss";
import Home from "@/pages/Home/Home";

const UPDATE_INTERVAL = 1000;

function App() {
  const [sources, setSources] = useState([]);
  const [streams, setStreams] = useState([]);
  const [zones, setZones] = useState([]);

  const update = () => {
    fetch(`/api`)
      .then((res) => res.json())
      .then((data) => {
        setSources(data.sources);
        setStreams(data.streams);
        setZones(data.zones);
      });
  };

  if (sources.length == 0 || streams.length == 0 || zones.length == 0) {
    return (
      useEffect(() => {
        const interval = setInterval(() => {
          update();
        }, UPDATE_INTERVAL);
        return () => clearInterval(interval);
      }, []),
      (<h1>Loading...</h1>)
    );
  }

  return (
    useEffect(() => {
      const interval = setInterval(() => {
        update();
      }, UPDATE_INTERVAL);
      return () => clearInterval(interval);
    }, []),
    (
      <div className="app">
        <Home sources={sources} zones={zones} />
      </div>
    )
  );
}

export default App;
