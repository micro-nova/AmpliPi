import { useStatusStore } from "./App"
import { useEffect } from "react"
import { useInterval } from "./hooks/useInterval"
import LoadingPage from "./pages/LoadingPage/LoadingPage"

const UPDATE_INTERVAL = 1500

const Poller = ({ children }) => {
  const isLoaded = useStatusStore((s) => s.loaded)
  const disconnected = useStatusStore((s) => s.disconnected)
  const update = useStatusStore((s) => s.fetch)

  useInterval(() => {
    update()
  }, UPDATE_INTERVAL)

  if (!isLoaded) {
    return <LoadingPage />
  }
  return children
}

export default Poller
