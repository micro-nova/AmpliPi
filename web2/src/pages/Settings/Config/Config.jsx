import "../PageBody.scss"
import "./Config.scss"
import PageHeader from "@/components/PageHeader/PageHeader"
import { useState } from "react"
import { Button, Divider } from "@mui/material"

const UploadConfig = (file) => {
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
    <div className="page-container">
      <PageHeader title="Config" onClose={onClose} />
      <div className="page-body">
        <div>
          Upload Config
          <div className="config-desc">{"Uploads the selected configuration file."}</div>
          <div>
            <input
              type="file"
              accept=".json,application/json"
              onChange={onChange}
            />
            <Button onClick={()=>UploadConfig(file)}>Upload</Button>
          </div>
        </div>
        <Divider />
        <div>
          Download Config
          <div className="config-desc">{"Downloads the current configuration."}</div>
          <Button onClick={DownloadConfig}>Download</Button>
        </div>
        <Divider />
        <div>
          Factory Config
          <div className="config-desc">{"Resets Amplipi to the factory default configuration. We recommend downloading the current configuration beforehand."}</div>
          <Button onClick={FactoryReset}>Reset</Button>
        </div>
        <Divider />
        <div>
          HW Reset
          <div className="config-desc">{"Resets the preamp hardware and controller software (does not reboot the Raspberry Pi-based controller)"}</div>
          <Button onClick={HWReset}>Reset</Button>
        </div>
        <Divider />
        <div>
          HW Reboot
          <div className="config-desc">{"Reboots the Raspberry Pi-based controller"}</div>
          <Button onClick={HWReboot}>Reboot</Button>
        </div>
        <Divider />
        <div>
          HW Shutdown
          <div className="config-desc">{"Trigger a shutdown of the Raspberry Pi-based controller"}</div>
          <Button onClick={HWShutdown}>Shutdown</Button>
        </div>
        <Divider />
      </div>
    </div>
  )
}

export default Config
