import { IsMobileApp } from "@/utils/MobileApp";

export default function ConfigDownload() {
    if (IsMobileApp()) {
        alert("This feature is not available in the mobile app.");
        return;
    }
    const response = fetch("/api");
    response.then((res) => {res.json().then((json) => {
        const element = document.createElement("a");
        const d = new Date();
        const file = new Blob([JSON.stringify(json, undefined, 2)], {
            type: "application/json",
        });
        element.href = URL.createObjectURL(file);
        element.download = `amplipi-config-${d.toJSON()}.json`;
        document.body.appendChild(element);
        element.click();
        });
    });
    return response;
};
