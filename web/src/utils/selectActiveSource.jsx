import { useStatusStore, usePersistentStore } from "@/App";

// Import and use this function on every page that relies on selected sources
// Currently, that means the Home and Player pages
export default function selectActiveSource(){ // Selects an active source, if the selected source is inactive
    const sources = useStatusStore((s) => s.status.sources);
    const selectedSource = usePersistentStore((s) => s.selectedSource);
    const setSelectedSource = usePersistentStore((s) => s.setSelectedSource);
    const autoselectSource = usePersistentStore((s) => s.autoselectSource);
    const setAutoselectSource = usePersistentStore((s) => s.setAutoselectSource);
    let run = false;

    // If selected source is not active, select the source with the lowest ID
    if(!sources || !sources[selectedSource] || !sources[selectedSource]["input"]){
        // While testing this script along with the one that autoselects the created source when adding a new source,
        // I found that there were times that a source could reach an undefined variable

        // Those won't reach prod on my watch, but this catch exists so that you don't need to go around commenting out
        // every instance of sources[x]["input"] in every file if you manage to reach that spot in your own development

        run = true;
        console.log("Source data missing, selecting a new source");
    }
    if(autoselectSource){
        if(run || sources[selectedSource]["input"] === "None"){
            for(let i = 0; i < sources.length; i++){
                if(sources[i]["input"] != "None"){
                    setSelectedSource(i);
                    break;
                }
            }
        }
    } else if (sources[selectedSource]["input"] !== "None"){
        // If presently selected source is valid/loaded, sources can be autoselected

        // autoselectSource is only set to false if the source that's been selected is currently loading,
        // so sources[selectedSource]["input"] will equal "None" for a limited time
        setAutoselectSource(true);
    }
}
