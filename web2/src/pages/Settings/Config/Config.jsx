import "./Config.scss"
import PageHeader from "@/components/PageHeader/PageHeader"
import Card from "@/components/Card/Card"
import { useState } from "react"
import { Button } from "@mui/material"

//TODO: test these

const UploadConfig = () => {
  fetch("/api/load", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(file),
  })
}

const DownloadConfig = () => {
  fetch("/api").then((response) => {
    response.json().then((json) => {
      const element = document.createElement("a")
      const file = new Blob([JSON.stringify(json, undefined, 2)], {
        type: "application/json",
      })
      element.href = URL.createObjectURL(file)
      element.download = "config.json"
      document.body.appendChild(element)
      element.click()
    })
  })
}

const FactoryReset = () => {
  fetch("/api/factory_reset", { method: "POST" })
}

const HWReset = () => {
  fetch("/api/reset", { method: "POST" })
}

const HWReboot = () => {
  fetch("/api/reboot", { method: "POST" })
}

const HWShutdown = () => {
  fetch("/api/shutdown", { method: "POST" })
}

const Config = ({ onClose }) => {
  const [file, setFile] = useState([])

  const onChange = (event) => {
    event.target.files[0].text().then((text) => {
      setFile(JSON.parse(text))
    })
  }

  return (
    <>
      <PageHeader title="Configuration and Reset" onClose={onClose} />
      <div className="config-body">
        <div>
          Upload Config
          <div>
            <input
              type="file"
              accept=".json,application/json"
              onChange={onChange}
            />
            <Button onClick={UploadConfig}>Upload</Button>
          </div>
        </div>
        <div>
          Download Config
          <Button onClick={DownloadConfig}>Download</Button>
        </div>
        <div>
          Factory Reset
          <Button onClick={FactoryReset}>Reset</Button>
        </div>
        <div>
          HW Reset
          <Button onClick={HWReset}>Reset</Button>
        </div>
        <div>
          HW Reboot
          <Button onClick={HWReboot}>Reboot</Button>
        </div>
        <div>
          HW Shutdown
          <Button onClick={HWShutdown}>Shutdown</Button>
        </div>
      </div>
    </>
  )
}

export default Config
