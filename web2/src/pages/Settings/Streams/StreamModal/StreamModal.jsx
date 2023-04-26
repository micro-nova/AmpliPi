import { useEffect, useState } from "react"
import Modal from "@/components/Modal/Modal"
import Card from "@/components/Card/Card"
import { CircularProgress, IconButton } from "@mui/material"
import DoneIcon from "@mui/icons-material/Done"
import DeleteIcon from "@mui/icons-material/Delete"
import "./StreamModal.scss"
import StreamTemplates from "../StreamTemplates.json"

const NAME_DESC =
  "This name can be anything - it will be used to select this stream from the source selection dropdown"
const DISABLED_DESC = "Don't show this stream in the input dropdown"

const TextField = ({ name, desc, defaultValue, onChange }) => {
  return (
    <div className="stream-field">
      <div className="stream-field-name">{name}</div>
      <input
        type="text"
        defaultValue={defaultValue}
        onChange={(e) => {
          onChange(e.target.value)
        }}
      />
      <div className="stream-field-desc">{desc}</div>
    </div>
  )
}

const BoolField = ({ name, desc, defaultValue, onChange }) => {
  return (
    <div className="stream-field">
      <div className="stream-field-name">{name}</div>
      <input
        type="checkbox"
        defaultChecked={defaultValue}
        onChange={(e) => {
          onChange(e.target.checked)
        }}
      />
      <div className="stream-field-desc">{desc}</div>
    </div>
  )
}

const InternetRadioSearch = ({ onChange }) => {
  const [host, setHost] = useState("")
  const [results, setResults] = useState([])
  const [query, setQuery] = useState("")

  const search = (name) => {
    setResults([<CircularProgress />])

    if (host === "") {
      return
    }

    fetch(`http://${host}/json/stations/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name }),
    }).then((res) =>
      res.json().then((s) => {
        setResults(
          s.slice(0, 10).map((s) => (
            <div
              className="internet-radio-result"
              key={s.changeuuid}
              onClick={() => {
                onChange({ name: s.name, url: s.url, logo: s.favicon })
              }}
            >
              <img src={s.favicon} className="internet-radio-image" />
              <div className="internet-radio-name">{s.name}</div>
            </div>
          ))
        )
      })
    )
  }

  return (
    useEffect(() => {
      fetch("http://all.api.radio-browser.info/json/servers").then((res) =>
        res.json().then(async (s) => {
          for (const i of s) {
            const res = await fetch(i.ip)
            if (res.ok && res.status === 200) {
              setHost(i.name)
              break
            }
          }
        })
      )
    }, []),
    (
      <div className="stream-field">
        <div className="stream-field-name">Search</div>
        <input type="text" onChange={(e) => setQuery(e.target.value)} />
        <input type="button" value="Search" onClick={(e) => search(query)} />
        <div className="stream-field-desc">
          Search for internet radio stations
        </div>
        <div className="radio-search-results">{results}</div>
      </div>
    )
  )
}

const StreamModal = ({ stream, onClose, apply, del }) => {
  const [streamFields, setStreamFields] = useState(
    JSON.parse(JSON.stringify(stream))
  ) // set streamFields to copy of stream

  const streamTemplate = StreamTemplates.filter(
    (t) => t.type === stream.type
  )[0]

  return (
    <Modal onClose={onClose}>
      <Card className="stream-card">
        <div>
          <div className="stream-name">{stream.name}</div>

          <div>
            <TextField
              name="Name"
              desc={NAME_DESC}
              defaultValue={streamFields.name}
              onChange={(v) => {
                setStreamFields({ ...streamFields, name: v })
              }}
            />
            {
              // Render fields from StreamFields.json
              streamTemplate.fields.map((field) => {
                switch (field.type) {
                  case "text":
                    return (
                      <TextField
                        key={field.name}
                        name={field.name}
                        desc={field.desc}
                        required={field.required}
                        defaultValue={streamFields[field.name]}
                        onChange={(v) => {
                          setStreamFields({ ...streamFields, [field.name]: v })
                        }}
                      />
                    )
                  case "bool":
                    return (
                      <BoolField
                        key={field.name}
                        name={field.name}
                        desc={field.desc}
                        defaultValue={streamFields[field.name]}
                        onChange={(v) => {
                          setStreamFields({ ...streamFields, [field.name]: v })
                        }}
                      />
                    )
                  case "internet-radio-search":
                    return (
                      <InternetRadioSearch
                        key={field.name}
                        onChange={(v) => {
                          setStreamFields({
                            ...streamFields,
                            ["name"]: v.name,
                            ["logo"]: v.logo,
                            ["url"]: v.url,
                          })
                        }}
                      />
                    )
                }
              })
            }
            <BoolField
              name="Disable"
              desc={DISABLED_DESC}
              defaultValue={streamFields.disabled}
              onChange={(v) => {
                setStreamFields({ ...streamFields, disabled: v })
              }}
            />
          </div>
        </div>
        <div className="stream-buttons">
          <IconButton
            onClick={() => {
              apply(streamFields)
              onClose()
            }}
          >
            <DoneIcon
              className="stream-button-icon"
              style={{ width: "3rem", height: "3rem" }}
            />
          </IconButton>
          <IconButton
            onClick={() => {
              if (del) del(streamFields)
              onClose()
            }}
          >
            <DeleteIcon
              className="stream-button-icon"
              style={{ width: "3rem", height: "3rem" }}
            />
          </IconButton>
        </div>
      </Card>
    </Modal>
  )
}

export default StreamModal
