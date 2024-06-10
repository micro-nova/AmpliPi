import React from "react";
import PropTypes from "prop-types";
import { CircularProgress } from "@mui/material";
import { Divider } from "@mui/material";
import Alert from "@mui/material/Alert";
import "./StreamModal.scss";
import StreamTemplates from "../StreamTemplates.json";
import ModalCard from "@/components/ModalCard/ModalCard";

const NAME_DESC =
  "This name can be anything - it will be used to select this stream from the source selection dropdown";
const DISABLED_DESC = "Don't show this stream in the input dropdown";
const RESTART_DESC = "Sometimes the stream gets into a bad state and neds to be restarted. If that happened to this stream, click this to restart the stream.";

// We're already using mui, why are we reinventing the wheel? https://mui.com/material-ui/react-text-field/
// if it's a matter of className control on the underlying components, that still works with the mui textfield with the InputLabelProps prop and other componentProps
const TextField = ({ name, desc, type="text", defaultValue, onChange }) => {

    return (
        <>
            <div className="stream-field">
                <div className="stream-field-name">{name}</div>
                <input
                    type={type}
                    defaultValue={defaultValue}
                    onChange={(e) => {
                        onChange(e.target.value);
                    }}
                />
                <div className="stream-field-desc">{desc}</div>
            </div>
            <Divider />
        </>
    );
};
TextField.propTypes = {
    name: PropTypes.string.isRequired,
    desc: PropTypes.string.isRequired,
    type: PropTypes.string,
    defaultValue: PropTypes.string,
    onChange: PropTypes.func.isRequired,
};

// this could be collapsed into TextField by adding a prop named something like "mode" or "type" with a switch dependant on it to return a version with checkbox or text
const BoolField = ({ name, desc, defaultValue, onChange }) => {
    return (
        <>
            <div>
                <div className="stream-field-bool">
                    <div className="stream-field-name">{name}</div>
                    <input
                        type="checkbox"
                        defaultChecked={defaultValue}
                        onChange={(e) => {
                            onChange(e.target.checked);
                        }}
                    />
                </div>
                <div className="stream-field-desc">{desc}</div>
            </div>
            <Divider />
        </>
    );
};
BoolField.propTypes = {
    name: PropTypes.string.isRequired,
    desc: PropTypes.string.isRequired,
    defaultValue: PropTypes.bool,
    onChange: PropTypes.func.isRequired,
};

const ButtonField = ({ name, text, onClick, desc }) => {
    return (
        <>
            <div className="stream-field-button">
                <div className="stream-field-name">{name}</div>
                <button onClick={onClick == undefined ? () => {} : onClick}>{text}</button>
            </div>
            <div className="stream-field-desc">{desc}</div>
            <Divider />
        </>
    );
};
ButtonField.propTypes = {
    name: PropTypes.string.isRequired,
    text: PropTypes.string.isRequired,
    desc: PropTypes.string.isRequired,
    onClick: PropTypes.func.isRequired,
};

const InternetRadioSearch = ({ onChange }) => {
    const [host, setHost] = React.useState("");
    const [results, setResults] = React.useState([]);
    const [query, setQuery] = React.useState("");

    const search = (name) => {
        setResults([<CircularProgress key={name} />]);

        if (host === "") {
            return;
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
                                onChange({ name: s.name, url: s.url, logo: s.favicon });
                            }}
                        >
                            <img src={s.favicon} className="internet-radio-image" />
                            <div className="internet-radio-name">{s.name}</div>
                        </div>
                    ))
                );
            })
        );
    };

    return (
        React.useEffect(() => {
            fetch("http://all.api.radio-browser.info/json/servers").then((res) =>
                res.json().then(async (s) => {
                    for (const i of s) {
                        const res = await fetch("https://" + i.name);
                        if (res.ok && res.status === 200) {
                            setHost(i.name);
                            break;
                        }
                    }
                })
            );
        }, []),
        (
            <div className="stream-field">
                <div className="stream-field-name">Search</div>
                <input type="text" onChange={(e) => setQuery(e.target.value)} />
                <input type="button" value="Search" onClick={() => search(query)} />
                <div className="stream-field-desc">
          Search for internet radio stations
                </div>
                <div className="radio-search-results">{results}</div>
            </div>
        )
    );
};

InternetRadioSearch.propTypes = {
    onChange: PropTypes.func.isRequired,
};
const StreamModal = ({ stream, onClose, apply, del }) => {
    const [streamFields, setStreamFields] = React.useState(
        JSON.parse(JSON.stringify(stream))
    ); // set streamFields to copy of stream

    const [errorMessage, setErrorMessage] = React.useState("");

    const streamTemplate = StreamTemplates.filter(
        (t) => t.type === stream.type
    )[0];

    return (
        <ModalCard
            onClose={onClose}
            header={stream.name}
            onDelete={() => {
                if (del) del(streamFields);
                onClose();
            }}
            onAccept={() => {
                apply(streamFields).then((response)=>{
                    if(response.ok)
                    {
                        onClose();
                    }
                    response.json().then((error)=>{setErrorMessage(error.detail)});
                });
            }}
        >
            <div>
                <TextField
                    name="Name"
                    desc={NAME_DESC}
                    defaultValue={streamFields.name}
                    onChange={(v) => {
                        setStreamFields({ ...streamFields, name: v });
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
                                        type={"text"}
                                        required={field.required}
                                        defaultValue={streamFields[field.name]}
                                        onChange={(v) => {
                                            setStreamFields({ ...streamFields, [field.name]: v });
                                        }}
                                    />
                                );
                            case "password":
                                return (
                                    <TextField
                                        key={field.name}
                                        name={field.name}
                                        desc={field.desc}
                                        type={"password"}
                                        required={field.required}
                                        defaultValue={streamFields[field.name]}
                                        onChange={(v) => {
                                            setStreamFields({ ...streamFields, [field.name]: v });
                                        }}
                                    />
                                );
                        case "bool":
                            return (
                                <BoolField
                                    key={field.name}
                                    name={field.name}
                                    desc={field.desc}
                                    defaultValue={streamFields[field.name]}
                                    onChange={(v) => {
                                        setStreamFields({ ...streamFields, [field.name]: v });
                                    }}
                                />
                            );
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
                                        });
                                    }}
                                />
                            );
                        }
                    })
                }
                <BoolField
                    name="Disable"
                    desc={DISABLED_DESC}
                    defaultValue={streamFields.disabled}
                    onChange={(v) => {
                        setStreamFields({ ...streamFields, disabled: v });
                    }}
                />

                <ButtonField
                    name="Restart"
                    text="Restart Stream"
                    desc={RESTART_DESC}
                    onClick={() => fetch("/api/streams/" + stream.id + "/restart",{
                        method: "POST"
                    })}
                />
                { errorMessage && <Alert severity="error" variant="filled">{errorMessage}</Alert>}
            </div>
        </ModalCard>
    );
};
StreamModal.propTypes = {
    stream: PropTypes.any.isRequired,
    onClose: PropTypes.func.isRequired,
    apply: PropTypes.func.isRequired,
    del: PropTypes.func.isRequired,
};

export default StreamModal;
