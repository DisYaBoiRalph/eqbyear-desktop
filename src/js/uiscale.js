export async function initUiScale(controls) {
    const tauri = window.__TAURI__;
    if (!tauri) return;

    let info;
    try {
        info = await tauri.core.invoke("get_ui_scale");
    } catch (e) {
        return;
    }

    const label = (percent) => `${Math.round(percent)}%`;
    const paint = (next) => {
        for (const { range, reset } of controls) {
            range.min = String(next.min_percent);
            range.max = String(next.max_percent);
            range.value = String(next.percent);
            reset.textContent = label(next.percent);
        }
    };
    const request = async (percent) => {
        try {
            paint(await tauri.core.invoke("set_ui_scale", { percent }));
        } catch (e) {
            /* keep the current scale */
        }
    };

    paint(info);
    for (const { box, range, reset } of controls) {
        range.addEventListener("input", () => {
            reset.textContent = label(Number(range.value));
        });
        // Apply on release: the slider rescales with the UI and would jump under the pointer.
        range.addEventListener("change", () => request(Number(range.value)));
        reset.addEventListener("click", () => request(100));
        box.hidden = false;
    }
    tauri.event.listen("ui-scale-changed", (event) => paint(event.payload));
}
