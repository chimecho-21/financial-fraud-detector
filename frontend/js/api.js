/* API 通信模块 */
// 使用相对路径 — 无论部署在哪都能自动匹配当前域名和端口
const API_BASE = '/api';

async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`请求失败: ${res.status}`);
    return res.json();
}

async function apiPost(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const err = await res.text();
        throw new Error(`分析失败: ${err}`);
    }
    return res.json();
}

async function apiUpload(file, companyName, industry) {
    const formData = new FormData();
    formData.append('file', file);
    if (companyName) formData.append('company_name', companyName);
    if (industry) formData.append('industry', industry);

    const res = await fetch(`${API_BASE}/analyze/upload`, {
        method: 'POST',
        body: formData,
    });
    if (!res.ok) {
        const err = await res.text();
        throw new Error(`上传分析失败: ${err}`);
    }
    return res.json();
}

async function loadSamples() {
    return apiGet('/samples');
}

async function analyzeSample(name) {
    return apiGet(`/sample/${name}`);
}

async function analyzeJSON(data) {
    return apiPost('/analyze/json', data);
}
