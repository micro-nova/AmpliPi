import React from "react";
import PropTypes from "prop-types";
import { create } from "zustand";
import { useStatusStore } from "@/App";
import { getSourceInputType } from "@/utils/getSourceInputType";
import produce from "immer";

import ModalCard from "@/components/ModalCard/ModalCard";
import "./CreatePresetModal.scss";

import Checkbox from "@mui/material/Checkbox";
import Switch from "@mui/material/Switch";
import FormControlLabel from "@mui/material/FormControlLabel";
import Box from "@mui/material/Box";

const setCheckedRecur = (dict, checked) => {
    dict.checked = checked;
    dict.content.forEach((it) => setCheckedRecur(it, checked));
};

const computeCheckedStateRecur = (dict) => {
    if (dict.content.length === 0) {
        return dict.checked;
    }

    let c = computeCheckedStateRecur(dict.content[0]);
    for (let i = 1; i < dict.content.length; i++) {
        let curr = computeCheckedStateRecur(dict.content[i]);
        if (c === "ind" || curr === "ind" || c !== curr) {
            c = "ind";
        }
    }
    dict.checked = c;
    return c;
};

const useTreeStore = create((set) => ({
    tree: null,
    setTree: (newTree) => {
        set({ tree: newTree });
    },
    setChecked: (path, checked) => {
        set(
            produce((s) => {
                // navigate to desired tree
                let curr = s.tree;
                for (const p of path) {
                    curr = curr.content[p];
                }
                // set checked on tree and all children recursively
                setCheckedRecur(curr, checked);

                // recompute checked state
                computeCheckedStateRecur(s.tree);
            })
        );
    },
}));

const baseDict = (open, name, content, payload = null) => {
    return {
        open: open,
        checked: "unchecked",
        name: name,
        content: content,
        payload: payload,
    };
};

const buildTreeDict = (status, showInactive = false) => {
    const dictWithOptions = (source) => {
    // grab zones that are playing this source
    // only take id, source_id, mute, vol as the rest is derived (i think) TODO verify
    // https://stackoverflow.com/questions/17781472/how-to-get-a-subset-of-a-javascript-objects-properties
        const zones_payload = status.zones
            .filter((zone) => zone.source_id === source.id)
            .map((zone) =>
                (({ id, source_id, mute, vol }) => ({ id, source_id, mute, vol }))(zone)
            );
        // only take id, source_id, mute, vol_delta
        const groups_payload = status.groups
            .filter((group) => group.source_id === source.id)
            .map((group) =>
                (({ id, source_id, mute, vol_delta }) => ({
                    id,
                    source_id,
                    mute,
                    vol_delta,
                }))(group)
            );
        const sources_payload = [(({ id, input }) => ({ id, input }))(source)];
        const name = `S${source.id + 1}: ${source.info.name}`;
        return baseDict(
            false,
            name,
            [
                baseDict(false, "Stream", [], { sources: sources_payload }),
                baseDict(false, "Volume", [], {
                    zones: zones_payload,
                    groups: groups_payload,
                }),
                // baseDict(false, 'Zones', []),
            ],
            {}
        );
    };

    const statusClone = JSON.parse(JSON.stringify(status));
    const sourceDicts = statusClone.sources
        .filter((source) => showInactive || getSourceInputType(source) !== "none")
        .map(dictWithOptions);
    const top = baseDict(false, "All", sourceDicts);
    return top;
};

const StructuredDictAsTree = ({ dict, depth = 0, path = [] }) => {
    const setChecked = useTreeStore((s) => s.setChecked);
    const checked = dict.checked;

    const handlePress = (e) => {
        setChecked(path, e.target.checked ? "checked" : "unchecked");
    };

    let entries = [];
    let i = 0;
    for (const d of dict.content) {
        entries.push(
            <StructuredDictAsTree
                key={i}
                dict={d}
                depth={depth + 1}
                path={[...path, i]}
            />
        );
        i += 1;
    }

    return (
        <>
            <Box sx={{ display: "flex", flexDirection: "column", ml: 3 * depth }}>
                <FormControlLabel
                    label={dict.name}
                    control={
                        <Checkbox
                            checked={checked === "checked"}
                            indeterminate={checked === "ind"}
                            onChange={handlePress}
                        />
                    }
                />
                {entries}
            </Box>
        </>
    );
};
StructuredDictAsTree.propTypes = {
    dict: PropTypes.array.isRequired,
    depth: PropTypes.number.isRequired,
    path: PropTypes.array.isRequired,
};
StructuredDictAsTree.defaultProps = {
    depth: 0,
    path: [],
};

const mergePayloads = (tree) => {
    let zones_merged = [];
    let groups_merged = [];
    let sources_merged = [];

    const p = tree.payload;
    if (p !== null && tree.checked === "checked") {
        if (p.zones !== undefined) zones_merged.push(...p.zones);
        if (p.groups !== undefined) groups_merged.push(...p.groups);
        if (p.sources !== undefined) sources_merged.push(...p.sources);
    }

    for (const subtree of tree.content) {
        const to_merge = mergePayloads(subtree);
        zones_merged.push(...to_merge.zones);
        groups_merged.push(...to_merge.groups);
        sources_merged.push(...to_merge.sources);
    }

    return {
        zones: zones_merged,
        groups: groups_merged,
        sources: sources_merged,
    };
};

const CreatePresetModal = ({ onClose }) => {
    const [name, setName] = React.useState("name");
    const status = useStatusStore((s) => s.status);
    const setTree = useTreeStore((s) => s.setTree);
    const tree = useTreeStore((s) => s.tree);

    React.useEffect(() => {
        const newTree = buildTreeDict(status);
        setTree(newTree);
    }, []);

    const savePreset = () => {
    // create preset
        fetch("/api/preset", {
            method: "POST",
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({
                name: name,
                state: mergePayloads(tree),
            }),
        });
    };
    // creation of tree is delayed due to React.useEffect, so early return is required
    if (tree === null) return <div />;

    return (
        <ModalCard
            onClose={onClose}
            header="Create Preset"
            onAccept={() => {
                savePreset();
                onClose();
            }}
            onCancel={onClose}
        >
            <div>Name</div>
            <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
            />
            <br />
            <div>Properties</div>
            <div>
                <FormControlLabel
                    label={"Show Inactive"}
                    control={
                        <Switch
                            onClick={(e) => setTree(buildTreeDict(status, e.target.checked))}
                        />
                    }
                />
            </div>
            <StructuredDictAsTree dict={tree} />
        </ModalCard>
    );
};
CreatePresetModal.propTypes = {
    onClose: PropTypes.func.isRequired,
};

export default CreatePresetModal;
