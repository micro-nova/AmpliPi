import spotify from "@/../static/imgs/spotify.png";
import dlna from "@/../static/imgs/dlna.png";
import bluetooth from "@/../static/imgs/bluetooth.png";
import fmradio from "@/../static/imgs/fmradio.png";
import shairport from "@/../static/imgs/shairport.png";
import pandora from "@/../static/imgs/pandora.png";
import plexamp from "@/../static/imgs/plexamp.png";
import lms from "@/../static/imgs/lms.png";
import internetradio from "@/../static/imgs/internet_radio.png";
import usb from "@/../static/imgs/usb.png";
import rca from "@/../static/imgs/rca_inputs.jpg";
import aux from "@/../static/imgs/aux_input.svg";

export const getIcon = (type) => {
  if (type === null || type === undefined) {
    return internetradio;
  }
  switch (type.toUpperCase()) {
    case "SPOTIFY":
      return spotify;

    case "SPOTIFYCONNECT":
      return spotify;

    case "DLNA":
      return dlna;

    case "BLUETOOTH":
      return bluetooth;

    case "FMRADIO":
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

    case "INTERNETRADIO":
      return internetradio;

    case "AUX":
      return aux;

    case "MEDIADEVICE":
      return usb;

    default:
      return internetradio;
  }
};
