import { useStatusStore } from "./App"
import { useEffect } from "react"
import { useInterval } from "./hooks/useInterval"
import LoadingPage from "./pages/LoadingPage/LoadingPage"

const UPDATE_INTERVAL = 1500

const Poller = ({ children }) => {
  const isLoaded = useStatusStore((s) => s.loaded)
  const disconnected = useStatusStore((s) => s.disconnected)
  const update = useStatusStore((s) => s.fetch)

  // update immediately at start
  useEffect(() => {
    update()
  }, [])

  // update periodically
  useInterval(() => {
    update()
  }, UPDATE_INTERVAL)

  if (!isLoaded || disconnected) {
    return <LoadingPage />
  }
  return children
}

export default Poller
