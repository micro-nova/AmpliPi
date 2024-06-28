export const getSourceInputType = (source) => {
    // can return:
    // none, rca, digital, unknown
    if (!source || !source.input || source.input == undefined) return "unknown";
    const input = source.input.toLowerCase();

    if (input === "none" || input === "" || input === "local") {
        return "none";
    }

    const split = input.split("=");
    if (split.length !== 2) {
        console.log(`WARNING: unknown source input: ${input}`);
        return "unknown";
    }

    if (split[1] < 1000) {
        return "rca";
    } else {
        return "digital";
    }
};
