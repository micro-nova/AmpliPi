import React from "react";
import Checkbox from "@mui/material/Checkbox";

export const IsMobileApp = () => {
    return window.isMobileApp;
};

export const IsSaved = () => {
    if (IsMobileApp()) return window.isSaved;
};

export const PostMessage = (message) => {
    if (IsMobileApp()) {
        window.ReactNativeWebView.postMessage(message);
    }
};

export const SaveURL = () => {
    PostMessage("save-ip");
};

export const UnsaveURL = () => {
    PostMessage("unsave-ip");
};

export function AlwaysConnect(){
    const [isSavedUrl, setIsSavedUrl] = React.useState(IsSaved());
    if(IsMobileApp()){
        return(
            <div>
                <text>Always connect to this Amplipi</text>
                <Checkbox
                    checked={isSavedUrl}
                    onChange={(e) => {
                        if (e.target.checked) {
                            SaveURL();
                        } else {
                            UnsaveURL();
                        }
                        setIsSavedUrl(e.target.checked);
                    }}
                />
            </div>
        )
    }
}
