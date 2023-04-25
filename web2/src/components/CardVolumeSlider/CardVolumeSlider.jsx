import Slider from "@mui/material/Slider"
import { useState, useEffect } from "react"
import "./CardVolumeSlider.scss"
import { getSourceZones } from "@/pages/Home/Home"
import { useStatusStore } from "@/App"
import VolumeSlider from "@/components/VolumeSlider/VolumeSlider"

const getPlayerVol = (sourceId, zones) => {
  let vol = 0
  let n = 0
  for (const i of getSourceZones(sourceId, zones)) {
    n += 1
    vol += i.vol_f
  }

  const avg = vol / n

  if (isNaN(avg)) {
    return 0
  } else {
    return avg
  }
}

export const applyPlayerVol = (vol, zones, sourceId, apply) => {
  let delta = vol - getPlayerVol(sourceId, zones)

  for (let i of getSourceZones(sourceId, zones)) {
    let set_pt = Math.max(0, Math.min(1, i.vol_f + delta))
    apply(i.id, set_pt)
  }
}

let sendingPacketCount = 0

const CardVolumeSlider = ({ sourceId }) => {
  const zones = useStatusStore((s) => s.status.zones)
  const setZonesVol = useStatusStore((s) => s.setZonesVol)
  const setZonesMute = useStatusStore((s) => s.setZonesMute)

  const setPlayerVolRaw = (vol) =>
    applyPlayerVol(vol, zones, sourceId, (zone_id, new_vol) => {
      sendingPacketCount += 1
      fetch(`/api/zones/${zone_id}`, {
        method: "PATCH",
        headers: {
          "Content-type": "application/json",
        },
        body: JSON.stringify({ vol_f: new_vol, mute: false }),
      }).then(() => {
        sendingPacketCount -= 1
      })
    })

  const setPlayerVol = (vol, force = false) => {
    if (sendingPacketCount <= 0 || force) {
      setPlayerVolRaw(vol)
    }
  }

  const value = getPlayerVol(sourceId, zones)

  const setValue = (vol) => {
    setZonesVol(vol, zones, sourceId)
    setZonesMute(false, zones, sourceId)
  }

  const mute = getSourceZones(sourceId, zones)
    .map((z) => z.mute)
    .reduce((a, b) => a && b, true)

  const setMute = (mute) => {
    setZonesMute(mute, zones, sourceId)
    fetch(`/api/zones`, {
      method: "PATCH",
      headers: {
        "Content-type": "application/json",
      },
      body: JSON.stringify({
        zones: getSourceZones(sourceId, zones).map((z) => z.id),
        update: { mute: mute },
      }),
    })
  }

  return (
    <VolumeSlider
      vol={value}
      mute={mute}
      setMute={setMute}
      setVol={(val, force = false) => {
        setPlayerVol(val, force)
        setValue(val)
      }}
    />
  )
}

export default CardVolumeSlider
