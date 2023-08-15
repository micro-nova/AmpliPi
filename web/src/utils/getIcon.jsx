import spotify from "@/assets/spotify.png";
import dlna from "@/assets/dlna.png";
import bluetooth from "@/assets/bluetooth.png";
import fmradio from "@/assets/fmradio.png";
import shairport from "@/assets/shairport.png";
import pandora from "@/assets/pandora.png";
import plexamp from "@/assets/plexamp.png";
import lms from "@/assets/lms.png";
import internetradio from "@/assets/internet_radio.png";
import rca from "@/assets/rca_inputs.jpg";

export const getIcon = (type) => {
    if (type === null || type === undefined) {
        return internetradio;
    }
    switch (type.toUpperCase()) {
    case "SPOTIFY":
        return spotify;

    case "DLNA":
        return dlna;

    case "BLUETOOTH":
        return bluetooth;

    case "FM RADIO":
        return fmradio;

    case "AIRPLAY":
        return shairport;

    case "PANDORA":
        return pandora;

    case "PLEXAMP":
        return plexamp;

    case "LMS":
        return lms;

    case "RCA":
        return rca;

    case "INTERNET RADIO":
        return internetradio;

    default:
        return internetradio;
    }
};
