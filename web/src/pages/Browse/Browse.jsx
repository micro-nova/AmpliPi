import { usePersistentStore, useStatusStore} from "@/App";
import "./Browse.scss";
import React, { useState, useRef } from "react";
import PropTypes from "prop-types";
import List from "@/components/List/List";
import ListItem from "@/components/List/ListItem/ListItem";
import { getIcon } from "@/utils/getIcon";
import { CircularProgress } from "@mui/material";
import StreamBar from "@/components/StreamBar/StreamBar";
import StatusBar from "@/components/StatusBars/StatusBar";
const Browse = () => {
    const selectedSourceId = usePersistentStore((s) => s.selectedSource);
    const [fileTree, setFileTree] = useState([]);
    const [errorOpen, setErrorOpen] = useState(false);
    const sid = useStatusStore((s) => s.status.sources[selectedSourceId].input.split("=")[1]);

    const [path, setPath] = useState(null);

    const errorText = useRef("");

    // This is what the browser is actually displaying. If this isn't the desired path, the list will reload.
    const pathCache = useRef(null);

    const dataHandler = (data) => {
        if(data.detail){
            if(data.detail[0].msg){
                throw new Error(data.detail[0].msg);
            } else {
                throw new Error(data.detail);
            }
        }
        setFileTree(data.items);
    };

    const errorHandler = ({name, message}) => {
        errorText.current = message;
        setErrorOpen(true);
    };

    const loadChildren = (item) => {
        if(!errorOpen){//Only run function if there is not an active error message to avoid React infinite state-changing loop error
            if(sid == null){ // If you manage to get to the browse page without a stream to select
                errorText.current = "No stream selected!";
                setErrorOpen(true);
            }
            else if (item == null) { // if item is null due initial load
                fetch(`/api/streams/browser/${sid}/browse`, {method: "post"} )
                .then(resp => resp.json())
                .then(dataHandler).catch(errorHandler);
            }
            else {
                fetch(`/api/streams/browser/${sid}/browse`,
                    {
                        headers: {
                            "content-type": "application/json",
                        },
                        method: "post",
                        datatype: "json",
                        body: JSON.stringify({
                            "item": item,
                        })
                    })
                .then(resp => resp.json())
                .then(dataHandler).catch(errorHandler);
            }

            pathCache.current = item;
            //TODO: make fetch and add children to item
        }
    };

    const reloading = useRef(false);

    const FileEntry = ({ item }) => {
        //TODO: make recursively render children

        const selectedSource = useStatusStore((s) => s.status.sources[selectedSourceId]);
        const stream = useStatusStore((s) => s.status.streams.filter(i => i.id == sid)[0]);

        let playing = selectedSource.info.station != null ? selectedSource.info.station : selectedSource.info.track;

        const setBrowsableStreamSong = useStatusStore((s) => s.setBrowsableStreamSong);
        const loading = useRef(false);
        return (
            <ListItem key={item.id}
                name={item.name}
                nameFontSize="1.5rem"
                onClick={() => {
                    loading.current = true;
                    reloading.current = true;
                    setBrowsableStreamSong(sid, item.id, setPath).then(()=>{
                        loading.current = false;
                        reloading.current = false;
                    });
                }}
                footer={loading.current ? <CircularProgress/> : (playing == item.name ? <div>Now Playing</div> : [])}>
                {<img src={item.img != "" ? item.img : getIcon(stream.type)} className="media-image" />}
            </ListItem>
        );
    };

    FileEntry.propTypes = {
        item: PropTypes.object,
    };
    if ((fileTree.length == 0 || pathCache.current != path) && !reloading.current) {
        loadChildren(path);
    }
    return (
        <div>
            <StreamBar sourceId={selectedSourceId}/>
            <List>
                {fileTree.map((i) => <FileEntry key={i.id} item={i} />)}
            </List>
            <StatusBar
                open={errorOpen}
                text={errorText.current}
                onClose={()=>{setErrorOpen(false);}}
            />
        </div>
    );
};

export default Browse;
