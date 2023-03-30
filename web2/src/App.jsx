import { useEffect, useState } from 'react'
import '@/App.scss'
import Home from '@/pages/Home/Home'

const UPDATE_INTERVAL = 1000

function App() {

  let sources = []
  let streams = []
  let zones = []

  const update = () => {
    fetch(`/api`).then(res => res.json()).then(data => {
      sources = data.sources
      streams = data.streams
      zones = data.zones
    })
  }

  return (
    useEffect(() => {
      const interval = setInterval(() => {
        update()
      }, UPDATE_INTERVAL)
      return () => clearInterval(interval)
    }, []),

    <div className='app'>
      <Home getSources={()=>{return sources}} getZones={()=>{return zones}}/>
    </div>

  )
}

export default App
