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
