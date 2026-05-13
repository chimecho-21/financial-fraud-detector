/* 主应用逻辑 */

let resultData = null;
let charts = [];

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initUpload();
    initManualInput();
    initSampleData();
    populateYearSelect();
    parseQueryParams();
});

function parseQueryParams() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('sample') === 'fraud') {
        setTimeout(() => startAnalysis('sample', 'fraud'), 300);
    }
}

/* === 选项卡切换 === */
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.getElementById('tab' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('active');
        });
    });
}

/* === 上传文件 === */
function initUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', e => { e.preventDefault(); uploadArea.classList.add('drag-over'); });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
    uploadArea.addEventListener('drop', e => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            onFileSelected(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) onFileSelected(fileInput.files[0]);
    });

    document.getElementById('uploadAnalyzeBtn').addEventListener('click', () => {
        const file = fileInput.files[0];
        if (!file) return;
        const name = document.getElementById('uploadCompanyName').value;
        const industry = document.getElementById('uploadIndustry').value;
        startAnalysis('upload', { file, name, industry });
    });
}

function onFileSelected(file) {
    const uploadArea = document.getElementById('uploadArea');
    const btn = document.getElementById('uploadAnalyzeBtn');
    uploadArea.querySelector('p').textContent = `已选择: ${file.name}`;
    uploadArea.querySelector('.upload-hint').textContent = `${(file.size / 1024).toFixed(1)} KB`;
    uploadArea.style.borderColor = '#3b82f6';
    btn.disabled = false;
}

/* === 手动录入 === */
function initManualInput() {
    document.getElementById('manualStartYear').addEventListener('change', renderManualFields);
    document.getElementById('manualYearCount').addEventListener('change', renderManualFields);
    document.getElementById('manualAnalyzeBtn').addEventListener('click', submitManual);

    // 填充年份下拉
    populateYearSelect();
    renderManualFields();
}

function populateYearSelect() {
    const sel = document.getElementById('manualStartYear');
    const current = new Date().getFullYear();
    sel.innerHTML = '';
    for (let y = current - 1; y >= current - 10; y--) {
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y + '年';
        if (y === current - 1) opt.selected = true;
        sel.appendChild(opt);
    }
}

const MANUAL_FIELDS = [
    { key: 'revenue', label: '营业收入', hint: '单位相同即可' },
    { key: 'cost_of_revenue', label: '营业成本' },
    { key: 'sg_and_a', label: '销售管理费用' },
    { key: 'depreciation', label: '折旧摊销' },
    { key: 'net_income', label: '净利润' },
    { key: 'interest_expense', label: '利息支出' },
    { key: 'income_tax', label: '所得税' },
    { key: 'operating_cash_flow', label: '经营活动现金流' },
    { key: 'total_assets', label: '总资产' },
    { key: 'current_assets', label: '流动资产' },
    { key: 'cash_and_equivalents', label: '货币资金' },
    { key: 'accounts_receivable', label: '应收账款' },
    { key: 'inventory', label: '存货' },
    { key: 'other_receivables', label: '其他应收款' },
    { key: 'fixed_assets', label: '固定资产' },
    { key: 'intangible_assets', label: '无形资产' },
    { key: 'total_liabilities', label: '总负债' },
    { key: 'current_liabilities', label: '流动负债' },
    { key: 'long_term_debt', label: '长期负债' },
    { key: 'total_equity', label: '股东权益' },
    { key: 'asset_impairment_loss', label: '资产减值损失' },
    { key: 'capital_expenditure', label: '资本支出' },
];

function renderManualFields() {
    const container = document.getElementById('manualFields');
    const startYear = parseInt(document.getElementById('manualStartYear').value);
    const yearCount = parseInt(document.getElementById('manualYearCount').value);

    container.innerHTML = '';
    for (let i = 0; i < yearCount; i++) {
        const year = startYear + i;
        const group = document.createElement('div');
        group.className = 'year-group';
        group.innerHTML = `<h4>${year} 年度</h4>`;

        let currentRow = document.createElement('div');
        currentRow.className = 'field-row';

        MANUAL_FIELDS.forEach((field, idx) => {
            if (idx > 0 && idx % 2 === 0) {
                group.appendChild(currentRow);
                currentRow = document.createElement('div');
                currentRow.className = 'field-row';
            }
            const item = document.createElement('div');
            item.className = 'field-item';
            item.innerHTML = `
                <label>${field.label}</label>
                <input type="number" step="any" id="manual_${year}_${field.key}" placeholder="0">
            `;
            currentRow.appendChild(item);
        });
        group.appendChild(currentRow);
        container.appendChild(group);
    }
}

function submitManual() {
    const name = document.getElementById('manualCompanyName').value.trim();
    if (!name) {
        alert('请输入公司名称');
        return;
    }
    const industry = document.getElementById('manualIndustry').value.trim() || '未知';
    const startYear = parseInt(document.getElementById('manualStartYear').value);
    const yearCount = parseInt(document.getElementById('manualYearCount').value);

    const fiscalYears = [];
    const statements = [];

    for (let i = 0; i < yearCount; i++) {
        const year = startYear + i;
        fiscalYears.push(year);
        const data = {};
        MANUAL_FIELDS.forEach(field => {
            const el = document.getElementById(`manual_${year}_${field.key}`);
            data[field.key] = el ? (parseFloat(el.value) || 0) : 0;
        });
        // 自动计算毛利和息税前利润
        data['gross_profit'] = data.revenue - data.cost_of_revenue;
        statements.push(data);
    }

    const payload = {
        company_name: name,
        industry: industry,
        fiscal_years: fiscalYears,
        statements: statements,
    };

    startAnalysis('json', payload);
}

/* === 示例数据 === */
async function initSampleData() {
    try {
        const samples = await loadSamples();
        const container = document.getElementById('sampleCards');
        container.innerHTML = '';
        samples.forEach(s => {
            const isFraud = s.key === 'fraud';
            const card = document.createElement('div');
            card.className = 'sample-card';
            card.innerHTML = `
                <h4>${s.name}</h4>
                <p class="meta">${s.industry} · ${s.years.join('-')}年</p>
                <span class="tag ${isFraud ? 'tag-fraud' : 'tag-normal'}">
                    ${isFraud ? '含造假特征' : '财务健康'}
                </span>
            `;
            card.addEventListener('click', () => startAnalysis('sample', s.key));
            container.appendChild(card);
        });
    } catch (e) {
        console.error('加载示例数据失败:', e);
    }
}

/* === 分析执行 === */
async function startAnalysis(mode, payload) {
    // 显示加载
    document.getElementById('inputSection').style.display = 'none';
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
    document.getElementById('loadingSection').style.display = 'block';

    try {
        let result;
        switch (mode) {
            case 'sample':
                result = await analyzeSample(payload);
                break;
            case 'json':
                result = await analyzeJSON(payload);
                break;
            case 'upload':
                result = await apiUpload(payload.file, payload.name, payload.industry);
                break;
            default:
                throw new Error('未知分析模式');
        }

        resultData = result;
        renderResults(result);
    } catch (e) {
        document.getElementById('loadingSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'block';
        document.getElementById('errorMessage').textContent = e.message;
    }
}

/* === 结果渲染 === */
function renderResults(data) {
    document.getElementById('loadingSection').style.display = 'none';
    document.getElementById('resultSection').style.display = 'block';

    // 基本信息
    document.getElementById('resultCompany').textContent = data.company_name;
    document.getElementById('resultYears').textContent = data.fiscal_years.join(' - ') + '年';

    // 清除旧图表
    charts.forEach(c => c.dispose());
    charts = [];

    // 风险等级
    const riskEl = document.getElementById('riskLevel');
    riskEl.textContent = `综合风险评级: ${data.risk_level}`;
    riskEl.style.color = data.risk_level_color;

    document.getElementById('riskSummary').textContent = data.summary;

    // 建议
    const recList = document.getElementById('recommendations');
    recList.innerHTML = '';
    data.recommendations.forEach(r => {
        const li = document.createElement('li');
        li.textContent = r;
        recList.appendChild(li);
    });

    // 仪表盘
    charts.push(renderGauge('scoreGauge', data.composite_score, data.risk_level, data.risk_level_color));

    // M-Score
    if (data.m_score) {
        document.getElementById('mScoreValue').textContent = data.m_score.m_score.toFixed(3);
        const statusEl = document.getElementById('mScoreStatus');
        statusEl.textContent = data.m_score.is_manipulator ? '⚠️ 存在操纵嫌疑' : '✅ 正常';
        statusEl.style.color = data.m_score.is_manipulator ? '#ef4444' : '#22c55e';
        document.getElementById('mScoreDetail').textContent = data.m_score.description;
        charts.push(renderMSpider('mScoreChart', data.m_score));
    }

    // Z-Score
    if (data.z_score) {
        document.getElementById('zScoreValue').textContent = data.z_score.z_score.toFixed(3);
        const statusEl = document.getElementById('zScoreStatus');
        const zoneColors = { '安全区': '#22c55e', '灰色区': '#eab308', '危险区': '#ef4444' };
        statusEl.textContent = `📍 ${data.z_score.zone}`;
        statusEl.style.color = zoneColors[data.z_score.zone] || '#6b7280';
        document.getElementById('zScoreDetail').textContent = data.z_score.description;
        const zThreshold = data.z_score.z_score < 1.81 ? 1.81 : 2.99;
        const barChartDom = document.createElement('div');
        barChartDom.style.height = '80px';
        document.querySelector('#zScoreCard .result-chart').appendChild(barChartDom);
        charts.push(renderSimpleBar(barChartDom.id || 'zScoreBar', data.z_score.z_score, zThreshold,
            zoneColors[data.z_score.zone] || '#6b7280'));
    }

    // ML 结果
    if (data.ml_result) {
        const ml = data.ml_result;
        document.getElementById('mlValue').textContent = ml.model_available ? (ml.fraud_probability * 100).toFixed(1) + '%' : '未启用';
        const statusEl = document.getElementById('mlStatus');
        if (ml.model_available) {
            statusEl.textContent = ml.prediction;
            statusEl.style.color = ml.fraud_probability < 0.3 ? '#22c55e' : ml.fraud_probability < 0.6 ? '#f97316' : '#ef4444';
        } else {
            statusEl.textContent = '模型不可用';
            statusEl.style.color = '#6b7280';
        }
        document.getElementById('mlDetail').textContent = ml.description;
        charts.push(renderMLGauge('mlChart', ml.fraud_probability));
    }

    // 综合评分卡片
    document.getElementById('compositeValue').textContent = data.composite_score + ' 分';
    document.getElementById('compositeValue').style.color = data.risk_level_color;
    document.getElementById('compositeStatus').textContent = `风险等级: ${data.risk_level}`;
    document.getElementById('compositeStatus').style.color = data.risk_level_color;
    document.getElementById('compositeDetail').textContent = `基于 M-Score(35%) · Z-Score(15%) · 财务比率(30%) · ML(20%)`;

    // 雷达图
    if (data.ratio_analysis && data.ratio_analysis.dimensions) {
        charts.push(renderRadar('radarChart', data.ratio_analysis.dimensions));
    }

    // 指标详情
    renderIndicatorDetails(data);

    // 滚动到结果
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderIndicatorDetails(data) {
    const container = document.getElementById('indicatorsTable');

    if (data.ratio_analysis && data.ratio_analysis.dimensions) {
        let html = '';
        data.ratio_analysis.dimensions.forEach(dim => {
            html += `<h4 style="margin:16px 0 8px;color:var(--text2);font-size:.9rem;">
                        ${dim.dimension} (评分: ${dim.score})</h4>`;
            html += '<div class="indicator-grid">';
            dim.indicators.forEach(ind => {
                const signalColor = ind.signal === '危险' ? '#ef4444' :
                                   ind.signal === '警告' ? '#f97316' : '#22c55e';
                html += `
                    <div class="indicator-item">
                        <div class="indicator-info">
                            <div class="indicator-name">${ind.name}</div>
                            <div class="indicator-threshold">${ind.threshold}</div>
                            <div style="font-size:.75rem;color:${signalColor};">${ind.detail}</div>
                        </div>
                        <div class="indicator-score" style="color:${signalColor};">${ind.score}</div>
                    </div>
                `;
            });
            html += '</div>';
        });
        container.innerHTML = html;
    } else {
        container.innerHTML = '<p style="color:var(--text2);">暂无详细指标数据</p>';
    }
}
