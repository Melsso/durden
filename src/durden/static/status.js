(function(){
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const statusModel = document.getElementById('statusModel');
    const statusMeta = document.getElementById('statusMeta');
    const uptimeEl = document.getElementById('uptime');
    const modelSelect = document.getElementById('modelSelect');
    const liveBadge = document.getElementById('liveBadge');
    const liveText = document.getElementById('liveText');

    const POLL_FAST_MS = 3000;
    const POLL_SLOW_MS = 15000;

    const state = window.durdenStatus = {
        online: false,
        ready: false,
        failed: false,
        models: [],
    };

    let serverStartTime = null;
    let renderedModels = '';
    let timer = null;
    const pageLoadTime = Date.now();

    function emit() {
        document.dispatchEvent(new CustomEvent('durden:status', { detail: { ...state } }));
    }

    function pad(n) { return n.toString().padStart(2, '0'); }

    function updateUptime() {
        if (!uptimeEl || !state.online) return;
        const base = serverStartTime !== null ? serverStartTime : pageLoadTime;
        const s = Math.max(0, Math.floor((Date.now() - base) / 1000));
        const hh = Math.floor(s / 3600), mm = Math.floor((s % 3600) / 60), ss = s % 60;
        uptimeEl.textContent = `${pad(hh)}:${pad(mm)}:${pad(ss)}`;
    }
    setInterval(updateUptime, 1000);

    function setStatusText(text, cls) {
        if (!statusText) return;
        statusText.classList.remove('status-ok', 'status-off', 'status-loading');
        statusText.classList.add(cls);
        statusText.textContent = text;
    }

    function setDot(cls) {
        if (!statusDot) return;
        statusDot.classList.remove('offline', 'loading');
        if (cls) statusDot.classList.add(cls);
    }

    function setSelectMessage(message) {
        if (!modelSelect) return;
        renderedModels = '';
        modelSelect.replaceChildren(new Option(message, ''));
        modelSelect.disabled = true;
    }

    function populateModelSelect(models) {
        const key = models.join('|');

        if (modelSelect && key !== renderedModels) {
            const previous = modelSelect.value;
            modelSelect.replaceChildren(...models.map(name => new Option(name, name)));
            modelSelect.value = models.includes(previous) ? previous : models[0];
            renderedModels = key;
        }
        if (modelSelect) modelSelect.disabled = !models.length;

        if (statusModel) {
            statusModel.textContent = (modelSelect && modelSelect.value) || models[0] || '—';
        }
    }

    function applyOnline(data) {
        state.online = true;
        state.ready = !!data.model_state;
        state.failed = !!data.model_error;
        state.models = data.models || [];

        if (liveBadge) liveBadge.classList.remove('offline');
        if (liveText) liveText.textContent = 'ONLINE';

        if (data.started_at) {
            const parsed = Date.parse(data.started_at);
            if (!isNaN(parsed)) serverStartTime = parsed;
        }
        if (statusMeta) statusMeta.textContent = `v${data.version} · ${data.environment}`;
        if (state.ready) {
            setDot(null);
            setStatusText('● OPERATIONAL', 'status-ok');
            populateModelSelect(state.models);
        } else if (state.failed) {
            setDot('offline');
            setStatusText('● MODEL ERROR', 'status-off');
            if (statusModel) statusModel.textContent = '—';
            setSelectMessage('Models failed to load');
        } else {
            setDot('loading');
            setStatusText('● LOADING MODELS', 'status-loading');
            if (statusModel) statusModel.textContent = '—';
            setSelectMessage('Loading models…');
        }
        updateUptime();
    }

    function applyOffline() {
        state.online = false;
        state.ready = false;
        state.failed = false;
        state.models = [];

        setDot('offline');
        setStatusText('● OFFLINE', 'status-off');
        if (liveBadge) liveBadge.classList.add('offline');
        if (liveText) liveText.textContent = 'OFFLINE';
        if (uptimeEl) uptimeEl.textContent = '—';
        if (statusModel) statusModel.textContent = '—';
        if (statusMeta) statusMeta.textContent = '—';
        setSelectMessage('No models available');
    }

    async function loadStatus() {
        clearTimeout(timer);
        if (document.hidden) return;

        try {
            const res = await fetch('/status', { cache: 'no-store' });
            if (!res.ok) throw new Error('status ' + res.status);
            applyOnline(await res.json());
        } catch (err) {
            console.error('Failed to load /status', err);
            applyOffline();
        }

        emit();
        timer = setTimeout(loadStatus, state.online && state.ready ? POLL_SLOW_MS : POLL_FAST_MS);
    }

    if (modelSelect) {
        modelSelect.addEventListener('change', () => {
            if (statusModel) statusModel.textContent = modelSelect.value || '—';
        });
    }

    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) loadStatus();
    });

    loadStatus();
})();