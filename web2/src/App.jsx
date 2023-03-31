import { useEffect, useState } from "react";
import { useCookies } from 'react-cookie';
import "@/App.scss";
import Home from "@/pages/Home/Home";
import MenuBar from "./components/MenuBar/MenuBar";

const UPDATE_INTERVAL = 1000;

function App() {
  const [status, setStatus] = useState(null);
  // const [cookies, setCookie] = useCookies(['selected'])
  const [selectedId, setSelectedId] = useState(0);
  const [selectedPage, setSelectedPage] = useState(0);


  const update = () => {
    fetch(`/api`)
      .then((res) => res.json())
      .then((data) => {
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

  return (
    useEffect(() => {
      const interval = setInterval(() => {
        update();
      }, UPDATE_INTERVAL);
      return () => clearInterval(interval);
    }, []),
    (
      <div className="app">
        <Home status={status} selectedId={selectedId} setSelectedId={setSelectedId} />
        <MenuBar pageNumber={selectedPage} onChange={(n)=>{console.log(`changing page to ${n}`); setSelectedPage(n)}}/>
      </div>
    )
  );
}

export default App;
