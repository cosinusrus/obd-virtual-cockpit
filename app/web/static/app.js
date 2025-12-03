async function apiGet(path) {
    const res = await fetch(path);
    if (!res.ok) {
        throw new Error(await res.text());
    }
    return res.json();
}

async function apiPost(path, body) {
    const res = await fetch(path, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: body ? JSON.stringify(body) : null
    });
    if (!res.ok) {
        throw new Error(await res.text());
    }
    try {
        return await res.json();
    } catch {
        return {};
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const statusBtn = document.getElementById("refresh-status");
    const statusOut = document.getElementById("status-output");

    const elmBtn = document.getElementById("btn-elm-init");
    const elmLog = document.getElementById("elm-log");

    const vinBtn = document.getElementById("btn-read-vin");
    const vinOut = document.getElementById("vin-output");

    const pollVin = document.getElementById("poll-vin");
    const pollPids = document.getElementById("poll-pids");
    const pollInterval = document.getElementById("poll-interval");
    const pollStart = document.getElementById("btn-start-poll");
    const pollStop = document.getElementById("btn-stop-poll");
    const pollOut = document.getElementById("poll-output");

    const cmdInput = document.getElementById("cmd-input");
    const cmdBtn = document.getElementById("btn-send-cmd");
    const cmdOut = document.getElementById("cmd-output");

    statusBtn.addEventListener("click", async () => {
        statusOut.textContent = "Загрузка...";
        try {
            const data = await apiGet("/api/status");
            statusOut.textContent = JSON.stringify(data, null, 2);
        } catch (e) {
            statusOut.textContent = "Ошибка: " + e.message;
        }
    });

    elmBtn.addEventListener("click", async () => {
        elmLog.textContent = "Инициализация...";
        try {
            const data = await apiPost("/api/elm/init", {});
            elmLog.textContent = data.log || JSON.stringify(data, null, 2);
        } catch (e) {
            elmLog.textContent = "Ошибка: " + e.message;
        }
    });

    vinBtn.addEventListener("click", async () => {
        vinOut.textContent = "Чтение VIN...";
        try {
            const data = await apiGet("/api/vin/read");
            vinOut.textContent = JSON.stringify(data, null, 2);
        } catch (e) {
            vinOut.textContent = "Ошибка: " + e.message;
        }
    });

    pollStart.addEventListener("click", async () => {
        pollOut.textContent = "Старт опроса...";
        const pids = pollPids.value.split(",").map(s => s.trim()).filter(Boolean);
        const body = {
            vin: pollVin.value || null,
            pids,
            interval: parseFloat(pollInterval.value || "1.0"),
        };
        try {
            const data = await apiPost("/api/polling/start", body);
            pollOut.textContent = JSON.stringify(data, null, 2);
        } catch (e) {
            pollOut.textContent = "Ошибка: " + e.message;
        }
    });

    pollStop.addEventListener("click", async () => {
        pollOut.textContent = "Остановка опроса...";
        try {
            const data = await apiPost("/api/polling/stop", {});
            pollOut.textContent = JSON.stringify(data, null, 2);
        } catch (e) {
            pollOut.textContent = "Ошибка: " + e.message;
        }
    });

    cmdBtn.addEventListener("click", async () => {
        const cmd = cmdInput.value.trim();
        if (!cmd) return;
        cmdOut.textContent = "Отправка команды...";
        try {
            const data = await apiPost("/api/command?command=" + encodeURIComponent(cmd), {});
            cmdOut.textContent = JSON.stringify(data, null, 2);
        } catch (e) {
            cmdOut.textContent = "Ошибка: " + e.message;
        }
    });

    // Автообновление статуса при загрузке
    statusBtn.click();
});
