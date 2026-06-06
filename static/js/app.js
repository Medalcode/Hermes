// --- STATE ---
let currentColumns = [];
let numericColumns = [];
const DB_NAME = 'myna-session-db';
const LEGACY_DB_NAME = 'myna';
const STORE_NAME = 'sessions';
const ACTIVE_SESSION_KEY = 'active';

// --- NAVIGATION ---
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
    
    document.getElementById(tabId).classList.add('active');
    // Find li with onclick containing the tabId
    const navItems = document.querySelectorAll('.nav-links li');
    navItems.forEach(item => {
        if(item.getAttribute('onclick').includes(tabId)) {
            item.classList.add('active');
        }
    });
}

// --- API HELPERS ---
async function postData(url, formData) {
    const response = await fetch(url, {
        method: 'POST',
        body: formData
    });
    return response.json();
}

function openSessionDB(dbName = DB_NAME) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(dbName, 1);
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME);
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

async function loadLocalSession() {
    const readFromDb = async (dbName) => {
        const db = await openSessionDB(dbName);
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readonly');
            const req = tx.objectStore(STORE_NAME).get(ACTIVE_SESSION_KEY);
            req.onsuccess = () => resolve(req.result || null);
            req.onerror = () => reject(req.error);
        });
    };

    const currentSession = await readFromDb(DB_NAME);
    if (currentSession) return currentSession;
    return readFromDb(LEGACY_DB_NAME);
}

async function saveLocalSession(patch) {
    const db = await openSessionDB();
    const current = (await loadLocalSession()) || {};
    const next = { ...current, ...patch };
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const req = tx.objectStore(STORE_NAME).put(next, ACTIVE_SESSION_KEY);
        req.onsuccess = () => resolve(next);
        req.onerror = () => reject(req.error);
    });
}

async function clearLocalSession() {
    const db = await openSessionDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const req = tx.objectStore(STORE_NAME).delete(ACTIVE_SESSION_KEY);
        req.onsuccess = () => resolve();
        req.onerror = () => reject(req.error);
    });
}

function applySessionState(session, statusText = '') {
    if (!session) return;
    currentColumns = session.columns || [];
    numericColumns = session.numeric_columns || [];
    updateSelects(currentColumns, ['nullCols']);
    updateSelects(numericColumns, ['scaleCols', 'clusterCols', 'plotCol', 'plotX', 'plotY']);
    if (session.last_preview) {
        renderTable(session.last_preview, 'uploadPreview');
    }
    if (statusText) {
        document.getElementById('uploadStatus').innerText = statusText;
    }
}

function updateSelects(columns, selectIds, isNumeric=false) {
    selectIds.forEach(id => {
        const select = document.getElementById(id);
        const selected = Array.from(select.selectedOptions).map(opt => opt.value); // Keep selection if possible
        select.innerHTML = '';
        
        columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col;
            option.text = col;
            if(selected.includes(col)) option.selected = true;
            select.appendChild(option);
        });
    });
}

function renderTable(data, containerId) {
    if(!data || data.length === 0) {
        document.getElementById(containerId).innerHTML = '<p>No hay datos.</p>';
        return;
    }
    
    const cols = Object.keys(data[0]);
    let html = '<table><thead><tr>';
    cols.forEach(c => html += `<th>${c}</th>`);
    html += '</tr></thead><tbody>';
    
    data.forEach(row => {
        html += '<tr>';
        cols.forEach(c => html += `<td>${row[c]}</td>`);
        html += '</tr>';
    });
    html += '</tbody></table>';
    
    document.getElementById(containerId).innerHTML = html;
}

// --- HANDLERS ---

// 1. Upload
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerText = "Cargando...";
    
    try {
        const res = await postData('/api/upload', formData);
        
        if (res.error) {
            statusDiv.innerText = "Error: " + res.error;
            return;
        }
        
        statusDiv.innerText = `Carga Exitosa. Shape: (${res.shape[0]}, ${res.shape[1]})`;
        renderTable(res.preview, 'uploadPreview');
        
        // Update State
        currentColumns = res.columns;
        numericColumns = res.numeric_columns;
        await saveLocalSession({
            df_json: res.df_json,
            columns: res.columns,
            numeric_columns: res.numeric_columns,
            shape: res.shape,
            last_preview: res.preview
        });
        
        // Detect 'Cluster' if re-uploading processed file
        if(currentColumns.includes('Cluster') && !numericColumns.includes('Cluster')) {
             // Force Cluster to stay if we want, but typically upload resets state
        }

        // Update Dropdowns
        updateSelects(currentColumns, ['nullCols']);
        updateSelects(numericColumns, ['scaleCols', 'clusterCols', 'plotCol', 'plotX', 'plotY']);
        
    } catch (err) {
        console.error(err);
        statusDiv.innerText = "Error de conexión.";
    }
});

// 2. Clean Nulls
async function cleanNulls() {
    const cols = Array.from(document.getElementById('nullCols').selectedOptions).map(o => o.value);
    const method = document.getElementById('nullMethod').value;
    
    if(cols.length === 0) { alert("Seleccione columnas."); return; }
    
    const formData = new FormData();
    cols.forEach(c => formData.append('cols', c));
    formData.append('method', method);
    const localSession = await loadLocalSession();
    if (localSession?.df_json) formData.append('df_json', localSession.df_json);
    
    const res = await postData('/api/clean/nulls', formData);
    if (res.error) { alert(res.error); return; }
    document.getElementById('cleanStatus').innerText = res.message;
    if(res.preview) renderTable(res.preview, 'uploadPreview'); // Update preview
    if (res.df_json) {
        const updatedSession = await saveLocalSession({
            df_json: res.df_json,
            columns: res.columns || currentColumns,
            numeric_columns: res.numeric_columns || numericColumns,
            shape: res.shape,
            last_preview: res.preview || localSession?.last_preview
        });
        applySessionState(updatedSession);
    }
}

// 3. Scale
async function scaleData() {
    const cols = Array.from(document.getElementById('scaleCols').selectedOptions).map(o => o.value);
    const method = document.getElementById('scaleMethod').value;
    
    if(cols.length === 0) { alert("Seleccione columnas."); return; }
    
    const formData = new FormData();
    cols.forEach(c => formData.append('cols', c));
    formData.append('method', method);
    const localSession = await loadLocalSession();
    if (localSession?.df_json) formData.append('df_json', localSession.df_json);
    
    const res = await postData('/api/clean/scale', formData);
    if (res.error) { alert(res.error); return; }
    document.getElementById('cleanStatus').innerText = res.message;
    if(res.preview) renderTable(res.preview, 'uploadPreview');
    if (res.df_json) {
        const updatedSession = await saveLocalSession({
            df_json: res.df_json,
            columns: res.columns || currentColumns,
            numeric_columns: res.numeric_columns || numericColumns,
            shape: res.shape,
            last_preview: res.preview || localSession?.last_preview
        });
        applySessionState(updatedSession);
    }
}

// 4. Stats
async function loadStats() {
    const formData = new FormData();
    const localSession = await loadLocalSession();
    if (localSession?.df_json) formData.append('df_json', localSession.df_json);
    const res = await postData('/api/stats', formData);
    if(res.error) { alert(res.error); return; }
    
    // Simple markdown render for now, or just pre
    // Ideally we would parse the MD table to HTML, but text is fine
    let html = `<pre>${res.descriptive}</pre>`;
    
    if(res.correlation) {
         // Could render heatmap here or json table
         const corr = JSON.parse(res.correlation);
         // ... render corr table logic if needed ...
    }
    document.getElementById('statsOutput').innerHTML = html;
    if (res.df_json) {
        const updatedSession = await saveLocalSession({
            df_json: res.df_json,
            columns: res.columns || currentColumns,
            numeric_columns: res.numeric_columns || numericColumns,
            shape: res.shape
        });
        applySessionState(updatedSession);
    }
}

// 5. Cluster
async function runCluster() {
    const cols = Array.from(document.getElementById('clusterCols').selectedOptions).map(o => o.value);
    const k = document.getElementById('kSlider').value;
    
    if(cols.length < 2) { alert("Seleccione al menos 2 variables."); return; }
    
    const formData = new FormData();
    cols.forEach(c => formData.append('cols', c));
    formData.append('k', k);
    const localSession = await loadLocalSession();
    if (localSession?.df_json) formData.append('df_json', localSession.df_json);
    
    const res = await postData('/api/cluster', formData);
    if (res.error) { alert(res.error); return; }
    document.getElementById('clusterStatus').innerText = res.message;
    if(res.preview) {
        renderTable(res.preview, 'uploadPreview');
    }
    if (res.df_json) {
        const updatedSession = await saveLocalSession({
            df_json: res.df_json,
            columns: res.columns || currentColumns,
            numeric_columns: res.numeric_columns || numericColumns,
            shape: res.shape,
            last_preview: res.preview || localSession?.last_preview
        });
        applySessionState(updatedSession);
    }
}

// 6. Plot
function updatePlotInputs() {
    const type = document.getElementById('plotType').value;
    const col = document.getElementById('plotCol');
    const x = document.getElementById('plotX');
    const y = document.getElementById('plotY');
    
    col.style.display = 'none';
    x.style.display = 'none';
    y.style.display = 'none';
    
    if(type === 'distribution') {
        col.style.display = 'block';
    } else if (type === 'regression' || type === 'cluster') {
        x.style.display = 'block';
        y.style.display = 'block';
    }
    // correlation needs no inputs
}

async function generatePlot() {
    const type = document.getElementById('plotType').value;
    const formData = new FormData();
    formData.append('type', type);
    const localSession = await loadLocalSession();
    if (localSession?.df_json) formData.append('df_json', localSession.df_json);
    
    if(type === 'distribution') {
        formData.append('col', document.getElementById('plotCol').value);
    } else if (type === 'regression' || type === 'cluster') {
         formData.append('x', document.getElementById('plotX').value);
         formData.append('y', document.getElementById('plotY').value);
    }
    
    const res = await postData('/api/plot', formData);
    if(res.error) { alert(res.error); return; }
    
    Plotly.newPlot('mainPlot', res.data, res.layout);
}

// 7. Auto-Analyze
async function runAutoAnalyze() {
    const statusDiv = document.getElementById('autoAnalyzeStatus');
    statusDiv.innerText = "Analizando dataset... 🤖";
    const reportContainer = document.getElementById('autoAnalyzeReport');
    reportContainer.style.display = 'none';
    
    const formData = new FormData();
    const localSession = await loadLocalSession();
    if (localSession?.df_json) formData.append('df_json', localSession.df_json);
    
    const res = await postData('/api/auto-analyze', formData);
    if(res.error) { 
        statusDiv.innerText = "Error: " + res.error; 
        return; 
    }
    
    statusDiv.innerText = "¡Análisis completado!";
    renderAutoAnalyzeReport(res.report);
    
    if (res.df_json) {
        const updatedSession = await saveLocalSession({
            df_json: res.df_json,
            columns: res.columns || currentColumns,
            numeric_columns: res.numeric_columns || numericColumns,
            shape: res.shape
        });
        applySessionState(updatedSession);
    }
}

function renderAutoAnalyzeReport(report) {
    const container = document.getElementById('autoAnalyzeReport');
    let html = '';

    // 1. Diagnóstico
    if(report.diagnostico_dataset) {
        const diag = report.diagnostico_dataset;
        html += `<div class="card">
            <h3>📊 Perfil del Dataset</h3>
            <p><strong>Filas:</strong> ${diag.rows} | <strong>Columnas:</strong> ${diag.columns}</p>
            <p><strong>Variables Numéricas:</strong> ${diag.numeric_columns} | <strong>Categóricas:</strong> ${diag.categorical_columns}</p>
            <p><strong>Uso de Memoria:</strong> ${diag.memory_usage_mb} MB</p>
        </div>`;
    }

    // 2. Problemas (Issues)
    if(report.problemas_detectados && report.problemas_detectados.length > 0) {
        html += `<div class="card" style="border-left: 4px solid #ff4757;">
            <h3 style="color: #ff4757;">🚨 Problemas Detectados</h3>
            <ul>`;
        report.problemas_detectados.forEach(issue => {
            html += `<li><strong>${issue.column}</strong>: ${issue.issue}</li>`;
        });
        html += `</ul></div>`;
    } else {
        html += `<div class="card" style="border-left: 4px solid #2ed573;">
            <h3 style="color: #2ed573;">✅ Problemas Detectados</h3>
            <p>El dataset parece estar limpio de nulos y atípicos graves.</p>
        </div>`;
    }

    // 3. Recomendaciones de Transformación
    if(report.transformaciones_recomendadas && report.transformaciones_recomendadas.length > 0) {
        html += `<div class="card" style="border-left: 4px solid #ffa502;">
            <h3 style="color: #ffa502;">💡 Sugerencias de Limpieza y Transformación</h3>
            <ul>`;
        report.transformaciones_recomendadas.forEach(rec => {
            html += `<li><strong>${rec.column}:</strong> ${rec.recommendation} <em>(Razón: ${rec.reason})</em></li>`;
        });
        html += `</ul></div>`;
    }

    // 4. Insights de Negocio
    if(report.conclusiones_negocio && report.conclusiones_negocio.length > 0) {
        html += `<div class="card" style="border-left: 4px solid #3742fa; background-color: #f1f2f6;">
            <h3 style="color: #3742fa;">🧠 Conclusiones Analíticas (Insights)</h3>
            <ul>`;
        report.conclusiones_negocio.forEach(insight => {
            html += `<li>${insight}</li>`;
        });
        html += `</ul></div>`;
    }

    // 5. Modelos Sugeridos
    if(report.modelos_sugeridos && report.modelos_sugeridos.length > 0) {
        html += `<div class="card" style="border-left: 4px solid #2f3542;">
            <h3 style="color: #2f3542;">🤖 Sugerencias de Machine Learning</h3>
            <ul>`;
        report.modelos_sugeridos.forEach(mod => {
            html += `<li><strong>Tarea:</strong> ${mod.task}<br><strong>Algoritmos recomendados:</strong> ${mod.models.join(", ")}<br><em>${mod.reason}</em></li>`;
        });
        html += `</ul></div>`;
    }

    container.innerHTML = html;
    container.style.display = 'flex';
}

window.addEventListener('load', async () => {
    updatePlotInputs();
    try {
        const session = await loadLocalSession();
        if (session) {
            const shapeText = session.shape ? ` (${session.shape[0]}, ${session.shape[1]})` : '';
            applySessionState(session, `Sesión local restaurada${shapeText}.`);
        }
    } catch (error) {
        console.error('Error loading local session', error);
    }
});

document.getElementById('clearLocalSessionBtn')?.addEventListener('click', async () => {
    await clearLocalSession();
    currentColumns = [];
    numericColumns = [];
    updateSelects([], ['nullCols', 'scaleCols', 'clusterCols', 'plotCol', 'plotX', 'plotY']);
    document.getElementById('uploadPreview').innerHTML = '';
    document.getElementById('uploadStatus').innerText = 'Sesión local eliminada.';
});
