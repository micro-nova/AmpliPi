import './PresetsModal.scss'
import Modal from '@/components/Modal/Modal'
import Card from '@/components/Card/Card'
import { useStatusStore } from '@/App'
import { useState } from 'react'

const timeSince = (timeStamp) => {
    var now = new Date(),
        secondsPast = (now.getTime() - timeStamp) / 1000;
    if (secondsPast < 60) {
        return parseInt(secondsPast) + 's';
    }
    if (secondsPast < 3600) {
        return parseInt(secondsPast / 60) + 'm';
    }
    if (secondsPast <= 86400) {
        return parseInt(secondsPast / 3600) + 'h';
    }
    if (secondsPast > 86400) {
        day = timeStamp.getDate();
        month = timeStamp.toDateString().match(/ [a-zA-Z]*/)[0].replace(" ", "");
        year = timeStamp.getFullYear() == now.getFullYear() ? "" : " " + timeStamp.getFullYear();
        return day + " " + month + year;
    }
}

const PresetItem = ({ index, onClick, presetState }) => {
    const preset = useStatusStore((state) => state.status.presets[index])
    const name = preset.name
    const last_used = timeSince(new Date(preset.last_used * 1000)) // js expects milliseconds from epoch
    // const last_used = 0

    // show checkmark if presetState is 'done'
    // show spinner if presetState is 'loading'
    return (
        <div className="preset-item" onClick={() => onClick(index)}>
            <div className="preset-name-and-last-used">
                <div>{name}</div>
                <div className="preset-item-last-used">{last_used}</div>
            </div>

            {presetState === 'done' && <div className="preset-item-icon">✓</div>}
            {presetState === 'loading' && <div className="preset-item-icon">⏳</div>}
        </div>
    )
}
    

const PresetsModal = ({ onClose }) => {
    const presets = useStatusStore((state) => state.status.presets)
    const [presetStates, setPresetStates] = useState(presets.map((preset) => false))

    // resize presetStates (without overriding) if length changes
    if (presetStates.length > presets.length) {
        setPresetStates(presetStates.slice(0, presets.length))
    } else if (presetStates.length < presets.length) {
        setPresetStates([...presetStates, ...Array(presets.length - presetStates.length).fill(false)])
    }

    const apply = (index) => {
        setPresetStates(presetStates.map((state, i) => (i === index ? 'loading' : state)))
        const id = presets[index].id
        console.log(`/api/presets/${id}/load`)
        fetch(`/api/presets/${id}/load`, { method: 'POST',  accept: 'application/json' })
            .then(() => setPresetStates(presetStates.map((state, i) => (i === index ? 'done' : state))))
            .catch(() => setPresetStates(presetStates.map((state, i) => (i === index ? false : state))))
    }

    const presetItems = presets.map((preset, index) => (
        <PresetItem
            key={index}
            index={index}
            onClick={apply}
            presetState={presetStates[index]}
        />
    ))

    return (
        <Modal className="presets-modal" onClose={onClose}>
            <Card className="presets-modal-card">
                <div className="presets-modal-header">
                    Select Preset
                </div>
                <div className="presets-modal-body">
                    {presetItems}
                </div>
            </Card>
        </Modal>
    )
}

export default PresetsModal



