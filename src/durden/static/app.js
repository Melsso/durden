(function(){
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const fileCard = document.getElementById('fileCard');
    const fileThumb = document.getElementById('fileThumb');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const detectBtn = document.getElementById('detectBtn');
    const threshold = document.getElementById('threshold');
    const threshVal = document.getElementById('threshVal');

    const emptyState = document.getElementById('emptyState');
    const canvasWrap = document.getElementById('canvasWrap');
    const sourceImg = document.getElementById('sourceImg');
    const overlay = document.getElementById('overlay');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const inferenceTime = document.getElementById('inferenceTime');
    const inferenceMs = document.getElementById('inferenceMs');

    const objectsBody = document.getElementById('objectsBody');
    const objectsCount = document.getElementById('objectsCount');

    const modelSelect = document.getElementById('modelSelect');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const statusModel = document.getElementById('statusModel');
    const statusMeta = document.getElementById('statusMeta');

    let isOnline = false;
    let selectedFile = null;
    let lastDetections = [];
    let highlightIndex = -1;
    let serverStartTime = null;

    const palette = ['#f4c531', '#2f8fe0', '#8b5cf6', '#34c759', '#ff6b6b', '#26c6da', '#e07bd0'];
    const labelColors = {};
    function colorFor(label){
        if(!labelColors[label]){
            const idx = Object.keys(labelColors).length % palette.length;
            labelColors[label] = palette[idx];
        }
        return labelColors[label];
    }

    let startTime = Date.now();
    function pad(n){ return n.toString().padStart(2,'0'); }
    function updateUptime(){
        if (!isOnline) {
            document.getElementById('uptime').textContent = `—`;
            return;
        }
        const base = serverStartTime !== null ? serverStartTime : startTime;
        const s = Math.max(0, Math.floor((Date.now()-base)/1000));
        const hh = Math.floor(s/3600), mm = Math.floor((s%3600)/60), ss = s%60;
        document.getElementById('uptime').textContent = `${pad(hh)}:${pad(mm)}:${pad(ss)}`;
    }
    setInterval(updateUptime, 1000);
    updateUptime();

    async function loadStatus(){
        try {
            const res = await fetch('/status');
            if(!res.ok) throw new Error('status ' + res.status);
            const data = await res.json();
            if (data.model_state === true) {
                isOnline = true;
                statusDot.classList.remove('offline');
                statusText.classList.remove('status-off');
                statusText.classList.add('status-ok');
                statusText.textContent = '● OPERATIONAL';
            } else {
                isOnline = false;
                statusDot.classList.remove('offline');
                statusText.classList.remove('status-ok');
                statusText.classList.add('status-off');
                statusText.textContent = '● LOADING MODELS';
            }

            if(data.started_at){
                const parsed = Date.parse(data.started_at);
                if(!isNaN(parsed)) serverStartTime = parsed;
            }
        
            statusMeta.textContent = `v${data.version} · ${data.environment}`;
        
            populateModelSelect(data.models || []);
            updateUptime();
        } catch(err) {
            isOnline = false;
            statusDot.classList.add('offline');
            statusText.classList.remove('status-ok');
            statusText.classList.add('status-off');
            statusText.textContent = '● OFFLINE';

            statusModel.textContent = '—';
            statusMeta.textContent = '—';
            modelSelect.innerHTML = '<option value="">No models available</option>';
            modelSelect.disabled = true;
        }
    }
    
    function populateModelSelect(models){
        if (!models.length) {
            modelSelect.innerHTML = '<option value="">No models available</option>';
            modelSelect.disabled = true;
            statusModel.textContent = '—';
            return;
        }
        modelSelect.innerHTML = models
        .map(name => `<option value="${name}">${name}</option>`)
        .join('');
        modelSelect.disabled = false;
        modelSelect.value = models[0];
        statusModel.textContent = models[0];
    }
    
    modelSelect.addEventListener('change', () => {
        statusModel.textContent = modelSelect.value || '—';
    });
    
    loadStatus();
    async function pollStatus(){
        await loadStatus();
    }
    setInterval(pollStatus, 5000);
    
    threshold.addEventListener('input', () => {
        threshVal.textContent = parseFloat(threshold.value).toFixed(2);
        drawOverlay();
    });

    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('drag'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag');
        if(e.dataTransfer.files && e.dataTransfer.files[0]){
            handleFile(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener('change', (e) => {
        if(e.target.files && e.target.files[0]) handleFile(e.target.files[0]);
    });

    function formatBytes(bytes){
        if(bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
        return (bytes/(1024*1024)).toFixed(1) + ' MB';
    }

    function handleFile(file){
        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatBytes(file.size);
        const url = URL.createObjectURL(file);
        fileThumb.src = url;
        fileCard.classList.add('show');
        detectBtn.disabled = false;

        lastDetections = [];
        renderTable([]);
        inferenceTime.style.display = 'none';

        sourceImg.onload = () => {
            emptyState.style.display = 'none';
            canvasWrap.classList.add('show');
            drawOverlay();
        };
        sourceImg.src = url;
    }

    detectBtn.addEventListener('click', async () => {
        if(!selectedFile) return;
        loadingOverlay.classList.add('show');
        detectBtn.disabled = true;

        try{
            const form = new FormData();
            form.append('file', selectedFile);
            if(modelSelect.value){
                form.append('model', modelSelect.value);
            }

            const response = await fetch('/predict', {
                method: 'POST',
                body: form
            });

            if(!response.ok){
                throw new Error('Request failed with status ' + response.status);
            }

            const data = await response.json();
            lastDetections = data.detections || [];
            inferenceMs.textContent = Math.round(data.inference_time_ms) + 'ms';
            inferenceTime.style.display = 'block';

            renderTable(lastDetections);
            drawOverlay();
        }catch(err){
            console.error(err);
            objectsBody.innerHTML = `<tr class="empty-table-row"><td colspan="5">Detection failed: ${err.message}</td></tr>`;
        }finally{
            loadingOverlay.classList.remove('show');
            detectBtn.disabled = false;
        }
    });

    function renderTable(detections){
        objectsCount.textContent = `${detections.length} object${detections.length===1?'':'s'} detected`;
        if(detections.length === 0){
            objectsBody.innerHTML = '<tr class="empty-table-row"><td colspan="5">No detections yet</td></tr>';
            return;
        }
        objectsBody.innerHTML = '';
        detections.forEach((d, i) => {
            const color = colorFor(d.label);
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${i+1}</td>
                <td><span class="swatch" style="background:${color}"></span>${d.label}</td>
                <td class="conf-cell">${(d.confidence*100).toFixed(1)}%</td>
                <td class="bbox-cell">[${d.bbox.join(', ')}]</td>
                <td>
                    <button class="eye-btn" data-idx="${i}" title="Highlight on image">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                </td>
            `;
            objectsBody.appendChild(tr);
        });

        objectsBody.querySelectorAll('.eye-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.idx, 10);
                highlightIndex = (highlightIndex === idx) ? -1 : idx;
                drawOverlay();
            });
        });
    }

    function drawOverlay(){
        if(!sourceImg.naturalWidth) return;
        const w = sourceImg.naturalWidth;
        const h = sourceImg.naturalHeight;
        overlay.width = w;
        overlay.height = h;
        const ctx = overlay.getContext('2d');
        ctx.clearRect(0,0,w,h);
        ctx.drawImage(sourceImg, 0, 0, w, h);

        const minConf = parseFloat(threshold.value);
        const fontSize = Math.max(14, Math.round(w * 0.013));
        ctx.font = `600 ${fontSize}px 'Segoe UI', Arial, sans-serif`;
        ctx.textBaseline = 'top';

        lastDetections.forEach((d, i) => {
            if(d.confidence < minConf) return;
            const [x1, y1, x2, y2] = d.bbox;
            const color = colorFor(d.label);
            const isHighlighted = highlightIndex === i;
            const lineWidth = Math.max(2, Math.round(w*0.0025)) * (isHighlighted ? 1.8 : 1);

            ctx.strokeStyle = color;
            ctx.lineWidth = lineWidth;
            if(isHighlighted){
                ctx.shadowColor = color;
                ctx.shadowBlur = 14;
            } else {
                ctx.shadowBlur = 0;
            }
            ctx.strokeRect(x1, y1, x2-x1, y2-y1);
            ctx.shadowBlur = 0;

            const label = `${d.label} ${d.confidence.toFixed(2)}`;
            const paddingX = 8;
            const textWidth = ctx.measureText(label).width;
            const labelHeight = fontSize + 10;

            ctx.fillStyle = color;
            ctx.fillRect(x1, Math.max(0, y1 - labelHeight), textWidth + paddingX*2, labelHeight);

            ctx.fillStyle = getContrastColor(color);
            ctx.fillText(label, x1 + paddingX, Math.max(0, y1 - labelHeight) + 5);
        });
    }

    function getContrastColor(hex){
        const c = hex.replace('#','');
        const r = parseInt(c.substr(0,2),16);
        const g = parseInt(c.substr(2,2),16);
        const b = parseInt(c.substr(4,2),16);
        const lum = (0.299*r + 0.587*g + 0.114*b)/255;
        return lum > 0.6 ? '#111111' : '#ffffff';
    }

    window.addEventListener('resize', drawOverlay);
})();