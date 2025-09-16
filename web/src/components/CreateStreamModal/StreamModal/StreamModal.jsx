import React from "react";
import PropTypes from "prop-types";
import "./StreamModal.scss";
import StreamTemplates from "../StreamTemplates.json";
import ModalCard from "@/components/ModalCard/ModalCard";
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import List from '@mui/material/List';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import ListItemText from '@mui/material/ListItemText';
import ListItemButton from '@mui/material/ListItemButton';
import Avatar from '@mui/material/Avatar';
import AlertBar from "@/components/StatusBars/AlertBar";


const NAME_DESC =
  "This name can be anything - it will be used to select this stream from the source selection dropdown";
const DISABLED_DESC = "Don't show this stream in the input dropdown";
const RESTART_DESC = "Sometimes the stream gets into a bad state and neds to be restarted. If that happened to this stream, click this to restart the stream.";

const TextArg = ({ name, desc, type="text", value, onChange, required, error }) => {

    return (
        <>
            <div className="stream-field">
                <TextField
                    className="stream-field-input"
                    type={type}
                    label={name}
                    error={error}
                    value={value ? value : ''}
                    onChange={(e) => {
                        onChange(e.target.value);
                    }}
                    required={required}
                    id={required? "outlined-required" : "outlined-basic"}
                    fullWidth
                />
                <div className="stream-field-desc">{desc}</div>
            </div>
        </>
    );
};
TextArg.propTypes = {
    name: PropTypes.string.isRequired,
    desc: PropTypes.string,
    type: PropTypes.string,
    value: PropTypes.string,
    onChange: PropTypes.func.isRequired,
    required: PropTypes.bool.isRequired,
    error: PropTypes.bool
};

// this could be collapsed into TextField by adding a prop named something like "mode" or "type" with a switch dependant on it to return a version with checkbox or text
const BoolField = ({ name, desc, value, onChange }) => {
    return (
        <>
            <div className="stream-field">
                <div className="stream-field-bool">
                    <div className="stream-field-name">{name}</div>
                    <Checkbox
                        checked={value}
                        onChange={(e) => {
                            onChange(e.target.checked);
                        }}
                    />
                </div>
                <div className="stream-field-desc">{desc}</div>
            </div>
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
            <div className="stream-field">
                <div className="stream-field-button">
                    <div className="stream-field-name">{name}</div>
                    <Button variant="outlined" onClick={onClick == undefined ? () => {} : onClick}>{text}</Button>
                </div>
                <div className="stream-field-desc">{desc}</div>
            </div>
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
    const [selectedUuid, setSelectedUuid] = React.useState("");

    const search = (name) => {
        // A blank search returns a 55MB JSON blob. At best, it reloads the list
        // once that completes and potentially clear out a successful search; at
        // worst, it'll mess with low performance machines.
        if (name === "") {
            return;
        }

        setResults([{name: "Loading..."}]);

        if (host === "") {
            return;
        }

        fetch(`https://${host}/json/stations/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: name }),
        }).then((res) =>
            res.json().then((s) => {
                setResults(s.slice(0, 10).valueOf());
            })
        );
    };

    return (
        React.useEffect(() => {
            // pinned this to fi1 since it appears to be the main server and the
            // HTTPS cert isn't valid for all.api.radio-browser.info
            fetch("https://fi1.api.radio-browser.info/json/servers").then((res) =>
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
            <>
                <div className="stream-field">
                    <div className="internet-radio-search">
                        <TextField
                            label="Search"
                            className="internet-radio-search-input"
                            fullWidth
                            sx={{ mr: '1rem' }}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={ (e) => {
                                if (e.key === 'Enter') {
                                    search(query);
                                }
                            }}
                        />
                        <Button variant="outlined" className="internet-radio-search-button" onClick={() => search(query)}>Search</Button>
                    </div>
                    <div className="stream-field-desc">
                        Search for internet radio stations
                    </div>
                    <List className="radio-search-results">
                        { results.map((s) => (
                            <ListItemButton
                                className="internet-radio-result"
                                key={s.changeuuid}
                                selected={selectedUuid == s.changeuuid}
                                onClick={() => {
                                    setSelectedUuid(s.changeuuid.valueOf());
                                    onChange({ name: s.name, url: s.url, logo: s.favicon });
                                }}
                            >
                                <ListItemAvatar>
                                    <Avatar variant="rounded"
                                        src={s.favicon ? s.favicon : null}
                                        alt={s.name}
                                        sx={{ height: '2rem' }}
                                        className="internet-radio-image"
                                    />
                                </ListItemAvatar>
                                <ListItemText className="internet-radio-name">{s.name}</ListItemText>
                            </ListItemButton>
                        ))}
                    </List>
                </div>
            </>
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
    const [hasError, setHasError] = React.useState(false); // Need a discrete hasError bool to trigger error
    const [renderAlertAnimation, setAlertAnimation] = React.useState(0); // Need a discrete hasError bool to trigger error

    const streamTemplate = StreamTemplates.filter(
        (t) => t.type === stream.type
    )[0];

    // prepend name field to template fields
    const templateFields = [{
        "key": "name",
        "name": "name",
        "title": "Name",
        "type": "text",
        "desc": NAME_DESC,
        "required": true
    }].concat(streamTemplate.fields);

    return (
        <ModalCard
            onClose={onClose}
            header={stream.name}
            footer={
                <AlertBar
                    renderAnimationState={renderAlertAnimation}
                    open={hasError}
                    onClose={() => {setHasError(false);}}
                    status={false}
                    text={errorMessage}
                />
            }

            // del is only used during edit, so use that to define when the modal should be in edit mode
            // Would use apply instead of del for the first one if apply didn't have a default as well
            buttons={[
                [ del ? "Edit Stream" : "Create Stream", () => {
                        // Check if all required fields are filled
                        for (const field of templateFields) {
                            if (field.required && (!(field.name.toLowerCase() in streamFields) || streamFields[field.name.toLowerCase()] === "")) {
                                setErrorField(field.name);
                                setErrorMessage(`Field ${field.name} is required`);
                                setAlertAnimation(renderAlertAnimation + 1);
                                setHasError(true);
                                return;
                            }
                        }
                        // Omit any fields that are simply empty. This permits Pydantic to cast to None,
                        // and then our constructors et al use their defaults.
                        // ref: https://github.com/pydantic/pydantic/discussions/2687
                        const filteredStreamFields = Object.fromEntries(
                            Object.entries(streamFields).filter( ([key, value]) => value !== "" )
                        );
                        apply(filteredStreamFields).then((response)=>{
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
                                    // We use the 'field' member to report an invalid field during stream validation,
                                    // but this isn't present on simple Pydantic model errors
                                    if(error.detail.field) {
                                        setErrorField(error.detail.field);
                                        setErrorMessage(error.detail.msg);
                                    } else if(error.detail[0]) {
                                        setErrorField(error.detail[0].loc[1]);
                                        // example: 'port: not a valid integer'
                                        setErrorMessage(`${error.detail[0].loc[1]}: ${error.detail[0].msg}`);
                                    } else {
                                        setErrorMessage("Unknown error");
                                    }
                                }
                                else{
                                    setErrorMessage("Unknown error");
                                }
                            });
                        });
                    }
                ],
                [
                    del ? "Delete" : "Cancel", () => {
                        if (del) del(streamFields);
                        onClose();
                    }
                ]
            ]}
        >
            <div>
                {
                    // Render fields from StreamFields.json
                    templateFields.map((field) => {
                        switch (field.type) {
                        case "text":
                            return (
                                <TextArg
                                    key={field.name}
                                    name={field.title}
                                    desc={field.desc}
                                    type={"text"}
                                    required={field.required == true}
                                    error={errorField.toLowerCase()==field.name.toLowerCase()}
                                    value={streamFields[field.name]}
                                    onChange={(v) => {
                                        setStreamFields({ ...streamFields, [field.name]: v });
                                    }}
                                />
                            );
                        case "password":
                            return (
                                <TextArg
                                    key={field.name}
                                    name={field.title}
                                    desc={field.desc}
                                    type={"password"}
                                    required={field.required == true}
                                    error={errorField.toLowerCase()==field.name.toLowerCase()}
                                    value={streamFields[field.name]}
                                    onChange={(v) => {
                                        setStreamFields({ ...streamFields, [field.name]: v });
                                    }}
                                />
                            );
                        case "bool":
                            return (
                                <BoolField
                                    key={field.name}
                                    name={field.title}
                                    desc={field.desc}
                                    value={streamFields[field.name]}
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
                    value={streamFields.disabled}
                    onChange={(v) => {
                        setStreamFields({ ...streamFields, disabled: v });
                    }}
                />

                {/* del is only used during edit, so use that to define when the modal should be in edit mode */}
                {del && <ButtonField
                    name="Restart"
                    text="Restart Stream"
                    desc={RESTART_DESC}
                    onClick={() => fetch("/api/streams/" + stream.id + "/restart",{
                        method: "POST"
                    })}
                />}
            </div>
        </ModalCard>
    );
};
StreamModal.propTypes = {
    stream: PropTypes.any.isRequired,
    onClose: PropTypes.func.isRequired,
    apply: PropTypes.func,
    del: PropTypes.func,
};
StreamModal.defaultProps = {
    apply: (stream) => {
        return fetch("/api/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(stream),
        });
    },
}

export default StreamModal;
