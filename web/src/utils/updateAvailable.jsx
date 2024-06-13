import { useStatusStore } from "@/App";

export function updateAvailable() {
    return useStatusStore( (s) =>
        s.status.info.version
            .split("+")[0]
            .localeCompare(s.status.info.latest_release, undefined, {
                numeric: true,
                sensitivity: "base",
            }) < 0 
    );
};
