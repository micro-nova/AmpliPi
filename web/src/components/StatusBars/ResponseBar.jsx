import React from "react";
import PropTypes from "prop-types";

import StatusBar from "./StatusBar";


export default function ResponseBar(props) {
    const {
        successText,
        response,
    } = props;

    const [open, setOpen] = React.useState(false);
    const [success, setSuccess] = React.useState(false);
    const text = React.useRef("");

    async function handleSuccess() {
        if(response != null){
            try {
                const res = await response;
                if (res.ok) {
                    setSuccess(true);
                    text.current = successText;
                } else {
                    const data = await res.json();
                    setSuccess(false);
                    text.current = data.detail.message;
                }
            } catch (error) {
                setSuccess(false);
                text.current = `An error occurred while FETCHing: ${error.message}`;
            }
            setOpen(true);
        }
    };

    React.useEffect(() => {
        handleSuccess();
    }, [response]);

    return(
        <StatusBar
            open={open}
            status={success}
            text={text.current}
            onClose={() => {setOpen(false);}}
        />
    );
}
ResponseBar.propTypes = {
    successText: PropTypes.string.isRequired,
    response: PropTypes.instanceOf(Promise).isRequired,
};

