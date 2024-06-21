export default async function handleLoad(response, setSuccess) {
    if(response.ok){
        setSuccess(true);
        return successText;
    } else {
        const data = await response.json();
        setSuccess(false);
        return data.detail.message;
    }
};
