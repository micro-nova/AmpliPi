import React from "react";
import PropTypes from "prop-types";
import { CircularProgress } from "@mui/material";
import { Divider } from "@mui/material";
import Alert from "@mui/material/Alert";
import "./StreamModal.scss";
import StreamTemplates from "../StreamTemplates.json";
import ModalCard from "@/components/ModalCard/ModalCard";
import TextField from '@mui/material/TextField';

const NAME_DESC =
  "This name can be anything - it will be used to select this stream from the source selection dropdown";
const DISABLED_DESC = "Don't show this stream in the input dropdown";
const RESTART_DESC = "Sometimes the stream gets into a bad state and neds to be restarted. If that happened to this stream, click this to restart the stream.";

const TextArg = ({ name, desc, type="text", defaultValue, onChange, required, error }) => {

    return (
        <>
            <div className="stream-field">
                <TextField
                    type={type}
                    label={name}
                    error={error}
                    defaultValue={defaultValue}
                    onChange={(e) => {
                        onChange(e.target.value);
                    }}
                    required={required}
                    id={required? "outlined-required" : "outlined-basic"}
                />
                <div className="stream-field-desc">{desc}</div>
            </div>
            <Divider />
        </>
    );
};
TextArg.propTypes = {
    name: PropTypes.string.isRequired,
    desc: PropTypes.string,
    type: PropTypes.string,
    defaultValue: PropTypes.string,
    onChange: PropTypes.func.isRequired,
    required: PropTypes.bool.isRequired,
    error: PropTypes.bool
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

    const [errorField, setErrorField] = React.useState("");

    const streamTemplate = StreamTemplates.filter(
        (t) => t.type === stream.type
    )[0];
    // HACK slight hack to ensure name is always present
    if(streamTemplate.fields.filter((field) => field.name === "Name").length === 0){
        streamTemplate.fields.unshift(
            {
                "name": "Name",
                "type": "name",
                "required": true
            });
    }

    return (
        <ModalCard
            onClose={onClose}
            header={stream.name}
            onDelete={() => {
                if (del) del(streamFields);
                onClose();
            }}
            onAccept={() => {
                // Check if all required fields are filled
                for (const field of streamTemplate.fields) {
                    if (field.required && (!(field.name.toLowerCase() in streamFields) || streamFields[field.name.toLowerCase()] === "")) {
                        setErrorField(field.name);
                        setErrorMessage(`Field ${field.name} is required`);
                        return;
                    }
                }
                apply(streamFields).then((response)=>{
                    if(response.ok)
                    {
                        setErrorField("");
                        onClose();
                    }
                    response.json().then((error)=>{
                        /*
                            Check type of error detail...
                            if it's a string it's some internal error
                            if it's an object it's a field error
                            otherwise we don't even know how to render it
                            TODO:   if/when we refactor API errors this probably
                                    also needs a refactor
                        */
                        if(typeof error.detail === "string"){
                            setErrorMessage(error.detail);
                        }
                        else if(typeof error.detail === "object"){
                            setErrorField(error.detail.field);
                            setErrorMessage(error.detail.msg);
                        }
                        else{
                            setErrorMessage("Unknown error");
                        }
                    });
                });
            }}
        >
            <div>
                {
                    // Render fields from StreamFields.json
                    streamTemplate.fields.map((field) => {
                        switch (field.type) {
                        case "name":
                            return (
                                <TextArg
                                    key="Name"
                                    name="Name"
                                    desc={NAME_DESC}
                                    defaultValue={streamFields.name}
                                    required={field.required == true}
                                    error={errorField.toLowerCase()==field.name.toLowerCase()}
                                    onChange={(v) => {
                                        setStreamFields({ ...streamFields, name: v });
                                    }}
                                />
                            );
                        case "text":
                            return (
                                <TextArg
                                    key={field.name}
                                    name={field.name}
                                    desc={field.desc}
                                    type={"text"}
                                    required={field.required == true}
                                    error={errorField.toLowerCase()==field.name.toLowerCase()}
                                    defaultValue={streamFields[field.name]}
                                    onChange={(v) => {
                                        setStreamFields({ ...streamFields, [field.name]: v });
                                    }}
                                />
                            );
                        case "password":
                            return (
                                <TextArg
                                    key={field.name}
                                    name={field.name}
                                    desc={field.desc}
                                    type={"password"}
                                    required={field.required == true}
                                    error={errorField.toLowerCase()==field.name.toLowerCase()}
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
    del: PropTypes.func,
};

export default StreamModal;
