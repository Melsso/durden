(function(){
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const fileCard = document.getElementById('fileCard');
    const fileThumb = document.getElementById('fileThumb');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileError = document.getElementById('fileError');
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

    const MAX_BYTES = 10 * 1024 * 1024;
    const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
    const INFERENCE_CONF = parseFloat(threshold.min) || 0.05;

    let selectedFile = null;
    let objectUrl = null;
    let lastDetections = [];
    let highlightIndex = -1;
    let busy = false;
    let appState = window.durdenStatus || { ready: false };

    const palette = ['#f4c531', '#2f8fe0', '#8b5cf6', '#34c759', '#ff6b6b', '#26c6da', '#e07bd0'];
    const labelColors = {};
    function colorFor(label) {
        if (!labelColors[label]) {
            const idx = Object.keys(labelColors).length % palette.length;
            labelColors[label] = palette[idx];
        }
        return labelColors[label];
    }

    function updateDetectBtn() {
        detectBtn.disabled = !(appState.ready && selectedFile && !busy);
    }

    document.addEventListener('durden:status', (e) => {
        appState = e.detail;
        updateDetectBtn();
    });

    function showFileError(message) {
        fileError.textContent = message || '';
        fileError.classList.toggle('show', !!message);
    }

    threshold.addEventListener('input', () => {
        threshVal.textContent = parseFloat(threshold.value).toFixed(2);
        renderTable();
        drawOverlay();
    });

    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInput.click();
        }
    });
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('drag'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) handleFile(e.target.files[0]);
        fileInput.value = '';
    });

    function formatBytes(bytes) {
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function handleFile(file) {
        if (!ALLOWED_TYPES.includes(file.type)) {
            showFileError('Unsupported file type. Use JPG, PNG or WEBP.');
            return;
        }
        if (file.size > MAX_BYTES) {
            showFileError(`File is too large (${formatBytes(file.size)}). Max size is 10 MB.`);
            return;
        }
        showFileError('');

        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatBytes(file.size);

        if (objectUrl) URL.revokeObjectURL(objectUrl);
        objectUrl = URL.createObjectURL(file);
        fileThumb.src = objectUrl;
        fileCard.classList.add('show');

        lastDetections = [];
        highlightIndex = -1;
        renderTable();
        inferenceTime.style.display = 'none';
        updateDetectBtn();

        sourceImg.onload = () => {
            emptyState.style.display = 'none';
            canvasWrap.classList.add('show');
            drawOverlay();
        };
        sourceImg.src = objectUrl;
    }

    async function errorFromResponse(response) {
        let detail = null;
        try {
            const body = await response.json();
            if (typeof body.detail === 'string') detail = body.detail;
        } catch (_) { /* non-JSON error body */ }
        return new Error(detail || 'Request failed with status ' + response.status);
    }

    detectBtn.addEventListener('click', async () => {
        if (!selectedFile || busy) return;
        busy = true;
        updateDetectBtn();
        loadingOverlay.classList.add('show');

        try {
            const form = new FormData();
            form.append('file', selectedFile);

            const params = new URLSearchParams({ conf: INFERENCE_CONF });
            if (modelSelect.value) params.set('model_name', modelSelect.value);

            const response = await fetch('/predict?' + params.toString(), {
                method: 'POST',
                body: form
            });

            if (!response.ok) throw await errorFromResponse(response);

            const data = await response.json();
            lastDetections = data.detections || [];
            highlightIndex = -1;
            inferenceMs.textContent = Math.round(data.inference_time_ms) + 'ms';
            inferenceTime.style.display = 'block';

            renderTable();
            drawOverlay();
        } catch (err) {
            console.error(err);
            lastDetections = [];
            drawOverlay();
            showTableMessage('Detection failed: ' + err.message);
        } finally {
            busy = false;
            loadingOverlay.classList.remove('show');
            updateDetectBtn();
        }
    });

    function visibleDetections() {
        const minConf = parseFloat(threshold.value);
        return lastDetections
            .map((d, i) => ({ d, i }))
            .filter(({ d }) => d.confidence >= minConf);
    }

    function showTableMessage(message) {
        const tr = document.createElement('tr');
        tr.className = 'empty-table-row';
        const td = document.createElement('td');
        td.colSpan = 5;
        td.textContent = message;
        tr.appendChild(td);
        objectsBody.replaceChildren(tr);
    }

    function cell(content, className) {
        const td = document.createElement('td');
        if (className) td.className = className;
        if (content instanceof Node) td.appendChild(content);
        else td.textContent = content;
        return td;
    }

    function renderTable() {
        const visible = visibleDetections();
        const hidden = lastDetections.length - visible.length;

        let summary = `${visible.length} object${visible.length === 1 ? '' : 's'} detected`;
        if (hidden > 0) summary += ` (${hidden} below threshold)`;
        objectsCount.textContent = summary;

        if (visible.length === 0) {
            showTableMessage(lastDetections.length === 0 ? 'No detections yet' : 'No detections above the threshold');
            return;
        }

        const rows = visible.map(({ d, i }, n) => {
            const tr = document.createElement('tr');
            const label = document.createElement('span');
            const swatch = document.createElement('span');
            swatch.className = 'swatch';
            swatch.style.background = colorFor(d.label);
            label.append(swatch, d.label);

            const eye = document.createElement('button');
            eye.type = 'button';
            eye.className = 'eye-btn';
            eye.title = 'Highlight on image';
            eye.setAttribute('aria-label', `Highlight ${d.label} on image`);
            eye.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>';
            eye.addEventListener('click', () => {
                highlightIndex = (highlightIndex === i) ? -1 : i;
                drawOverlay();
            });

            tr.append(
                cell(String(n + 1)),
                cell(label),
                cell((d.confidence * 100).toFixed(1) + '%', 'conf-cell'),
                cell('[' + d.bbox.join(', ') + ']', 'bbox-cell'),
                cell(eye)
            );
            return tr;
        });
        objectsBody.replaceChildren(...rows);
    }

    function drawOverlay(){
        if (!sourceImg.naturalWidth) return;
        const w = sourceImg.naturalWidth;
        const h = sourceImg.naturalHeight;
        overlay.width = w;
        overlay.height = h;
        const ctx = overlay.getContext('2d');
        ctx.clearRect(0,0,w,h);
        ctx.drawImage(sourceImg, 0, 0, w, h);

        const fontSize = Math.max(14, Math.round(w * 0.013));
        ctx.font = `600 ${fontSize}px 'Segoe UI', Arial, sans-serif`;
        ctx.textBaseline = 'top';

        visibleDetections().forEach(({ d, i }) => {
            const [x1, y1, x2, y2] = d.bbox;
            const color = colorFor(d.label);
            const isHighlighted = highlightIndex === i;
            const lineWidth = Math.max(2, Math.round(w*0.0025)) * (isHighlighted ? 1.8 : 1);

            ctx.strokeStyle = color;
            ctx.lineWidth = lineWidth;
            if (isHighlighted) {
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

    function getContrastColor(hex) {
        const c = hex.replace('#','');
        const r = parseInt(c.slice(0,2),16);
        const g = parseInt(c.slice(2,4),16);
        const b = parseInt(c.slice(4,6),16);
        const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        return lum > 0.6 ? '#111111' : '#ffffff';
    }

    window.addEventListener('resize', drawOverlay);
    updateDetectBtn();
})();