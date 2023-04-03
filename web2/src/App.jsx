import { useEffect, useState } from "react";
import { useCookies } from 'react-cookie';
import "@/App.scss";
import Home from "@/pages/Home/Home";
import Player from "@/pages/Player/Player";
import MenuBar from "./components/MenuBar/MenuBar";

const UPDATE_INTERVAL = 1000;

function App() {
  // funny string state lol
  const [statusOriginal, setStatusOriginal] = useState(null);
  const status = JSON.parse(statusOriginal)
  const setStatus = s => setStatusOriginal(JSON.stringify(s))

  const [selectedSource, setSelectedSource] = useState(0);
  const [selectedPage, setSelectedPage] = useState(0);



  const update = () => {
    fetch(`/api`)
      .then((res) => res.json())
      .then((data) => {
        // iterate through data and determine whats different
        const newStatus = Object.assign({}, status)

        setStatus(data);
      });
  };

  if (status == null) {
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

  // TODO: do some pages need 'on transition' events for initialization?
  const Page = () => {
      switch(selectedPage) {
      default:
        return <Home status={status} selectedSource={selectedSource} setSelectedSource={setSelectedSource} />
      case 1:
        return <Player status={status} setStatus={setStatus} selectedSource={selectedSource} />
      case 2:
        return <div></div>
      case 3:
        return <div></div>
    }
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
        <div style={{paddingBottom: '56px'}}>
          <Page />
        </div>
        <MenuBar pageNumber={selectedPage} onChange={(n)=>{console.log(`changing page to ${n}`); setSelectedPage(n)}}/>
      </div>
    )
  );
}

export default App;
