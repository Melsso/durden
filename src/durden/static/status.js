(function(){
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const statusModel = document.getElementById('statusModel');
    const statusMeta = document.getElementById('statusMeta');
    const uptimeEl = document.getElementById('uptime');
    const modelSelect = document.getElementById('modelSelect');
    const liveBadge = document.getElementById('liveBadge');
    const liveText = document.getElementById('liveText');
    const detectBtn = document.getElementById('detectBtn');

    let serverStartTime = null;
    let serverOnline = false;
    const pageLoadTime = Date.now();

    function pad(n) { return n.toString().padStart(2,'0'); }

    function updateUptime() {
        if (!uptimeEl) return;
        if (!serverOnline) return;
        const base = serverStartTime !== null ? serverStartTime : pageLoadTime;
        const s = Math.max(0, Math.floor((Date.now() - base) / 1000));
        const hh = Math.floor(s / 3600), mm = Math.floor((s % 3600) / 60), ss = s % 60;
        uptimeEl.textContent = `${pad(hh)}:${pad(mm)}:${pad(ss)}`;
    }
    setInterval(updateUptime, 1000);
    updateUptime();

    function populateModelSelect(models){
        if (!modelSelect) return;
        if (!models.length) {
            modelSelect.innerHTML = '<option value="">No models available</option>';
            modelSelect.disabled = true;
            if (statusModel) statusModel.textContent = '—';
            return;
        }
        modelSelect.innerHTML = models
        .map(name => `<option value="${name}">${name}</option>`)
        .join('');
        modelSelect.disabled = false;
        modelSelect.value = models[0];
        if (statusModel) statusModel.textContent = models[0];
    }

    async function loadStatus() {
        try {
            const res = await fetch('/status');
            if (!res.ok) throw new Error('status ' + res.status);
            const data = await res.json();

            serverOnline = true;

            if (statusDot) statusDot.classList.remove('offline');
            if (liveBadge) liveBadge.classList.remove('offline');
            if (liveText) liveText.textContent = 'LIVE';

            if (data.started_at) {
                const parsed = Date.parse(data.started_at);
                if(!isNaN(parsed)) serverStartTime = parsed;
            }

            if (statusMeta) statusMeta.textContent = `v${data.version} · ${data.environment}`;
            if (data.model_state) {
                if (statusDot) statusDot.classList.remove('loading');
                if (statusText) {
                    statusText.classList.remove('status-off', 'status-loading');
                    statusText.classList.add('status-ok');
                    statusText.textContent = '● OPERATIONAL';
                }
                if (detectBtn) detectBtn.disabled = false;
 
                populateModelSelect(data.models || []);
            } else {
                if (statusDot) statusDot.classList.add('loading');
                if (statusText) {
                    statusText.classList.remove('status-off', 'status-ok');
                    statusText.classList.add('status-loading');
                    statusText.textContent = '● LOADING MODELS';
                }
                if (statusModel) statusModel.textContent = '—';
                if (detectBtn) detectBtn.disabled = true;
 
                if (modelSelect) {
                    modelSelect.innerHTML = '<option value="">Loading models…</option>';
                    modelSelect.disabled = true;
                }
            }

            updateUptime();
        } catch(err) {
            console.error('Failed to load /status', err);
            serverOnline = false;

            if (statusDot) statusDot.classList.add('offline');
            if (statusText) {
                statusText.classList.remove('status-ok');
                statusText.classList.add('status-off');
                statusText.textContent = '● OFFLINE';
            }
            if (liveBadge) liveBadge.classList.add('offline');
            if (liveText) liveText.textContent = 'OFFLINE';
            if (uptimeEl) uptimeEl.textContent = '—';
            if (statusModel) statusModel.textContent = '—';
            if (statusMeta) statusMeta.textContent = '—';
            if (detectBtn) detectBtn.disabled = true;

            if (modelSelect) {
                modelSelect.innerHTML = '<option value="">No models available</option>';
                modelSelect.disabled = true;
            }
        }
    }

    if (modelSelect){
        modelSelect.addEventListener('change', () => {
        if (statusModel) statusModel.textContent = modelSelect.value || '—';
        });
    }

    loadStatus();
    setInterval(loadStatus, 4000);

})();