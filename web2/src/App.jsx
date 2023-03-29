import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './app.scss'
import { Card, CardHeader } from '@mui/material'
// import Card from '@mui/material/Card'
// import CardHeader from '@mui/material/CardHeader'

import PlayerCard from './components/PlayerCard/PlayerCard'

function App() {

  return (
    // <div className="box-thing">
    //   amplipi
    // </div>
    <div className='app'>
      <PlayerCard />
    </div>
    
  )
}

export default App
