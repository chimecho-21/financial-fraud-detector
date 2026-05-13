/* ECharts 图表渲染模块 */

function renderGauge(domId, score, riskLevel, color) {
    const chart = echarts.init(document.getElementById(domId));
    chart.setOption({
        series: [{
            type: 'gauge',
            startAngle: 220, endAngle: -40,
            min: 0, max: 100,
            splitNumber: 5,
            radius: '90%',
            pointer: { show: true, length: '55%', width: 4 },
            axisLine: {
                lineStyle: {
                    width: 20,
                    color: [
                        [0.2, '#22c55e'],
                        [0.4, '#eab308'],
                        [0.6, '#f97316'],
                        [0.8, '#ef4444'],
                        [1, '#7f1d1d'],
                    ]
                }
            },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            detail: {
                formatter: `{value} 分\n{riskLevel}`,
                rich: {
                    value: { fontSize: 32, fontWeight: 700, color: color, padding: [0,0,8,0] },
                    riskLevel: { fontSize: 14, color: color, fontWeight: 500 },
                },
                offsetCenter: [0, '45%'],
            },
            data: [{ value: score, name: riskLevel }],
        }]
    }, true);
    return chart;
}

function renderMSpider(domId, mScore) {
    const chart = echarts.init(document.getElementById(domId));
    const indicators = ['DSRI', 'GMI', 'AQI', 'SGI', 'DEPI', 'SGAI', 'LVGI', 'TATA'];
    const values = [mScore.dsri, mScore.gmi, mScore.aqi, mScore.sgi, mScore.depi, mScore.sgai, mScore.lvgi, mScore.tata];

    chart.setOption({
        radar: {
            indicator: indicators.map(name => ({ name, max: 3 })),
            shape: 'circle',
            center: ['50%', '50%'],
            radius: '65%',
        },
        series: [{
            type: 'radar',
            data: [{ value: values, name: 'M-Score 指标', areaStyle: { color: 'rgba(59,130,246,.2)' } }],
            symbol: 'none',
            lineStyle: { color: '#3b82f6', width: 2 },
        }]
    }, true);
    return chart;
}

function renderSimpleBar(domId, value, threshold, color) {
    const chart = echarts.init(document.getElementById(domId));
    const max = Math.max(Math.abs(value) * 1.5, threshold * 1.5, 5);
    chart.setOption({
        grid: { left: 0, right: 0, top: 0, bottom: 0 },
        xAxis: { show: false, min: -max, max: max },
        yAxis: { show: false },
        series: [
            {
                type: 'bar',
                data: [value],
                barWidth: 12,
                itemStyle: { color, borderRadius: 4 },
                label: { show: true, position: 'top', formatter: value.toFixed(2), fontSize: 10 },
            },
            {
                type: 'bar',
                data: [threshold],
                barWidth: 12,
                itemStyle: { color: '#d1d5db', borderRadius: 4, opacity: 0.3 },
            }
        ],
        animation: false,
    }, true);
    return chart;
}

function renderRadar(domId, dimensions) {
    const chart = echarts.init(document.getElementById(domId));
    const indicator = dimensions.map(d => ({
        name: d.dimension,
        max: 100,
    }));
    const values = dimensions.map(d => d.score);

    chart.setOption({
        radar: {
            indicator,
            shape: 'circle',
            radius: '60%',
            name: { textStyle: { fontSize: 12 } },
            splitArea: { areaStyle: { color: ['rgba(59,130,246,.02)', 'rgba(59,130,246,.06)'] } },
        },
        series: [{
            type: 'radar',
            data: [{
                value: values,
                name: '财务健康',
                areaStyle: { color: 'rgba(59,130,246,.2)' },
                lineStyle: { color: '#3b82f6', width: 2 },
                itemStyle: { color: '#3b82f6' },
            }],
            symbol: 'circle',
            symbolSize: 6,
        }],
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                const d = params.value;
                return params.name + '<br/>' + indicator.map((ind, i) =>
                    `${ind.name}: ${d[i]} 分`
                ).join('<br/>');
            }
        },
    }, true);
    return chart;
}

function renderMLGauge(domId, probability) {
    const chart = echarts.init(document.getElementById(domId));
    const color = probability < 0.3 ? '#22c55e' : probability < 0.6 ? '#f97316' : '#ef4444';

    chart.setOption({
        series: [{
            type: 'gauge',
            startAngle: 220, endAngle: -40,
            min: 0, max: 1,
            radius: '80%',
            pointer: { show: true, length: '50%', width: 3 },
            axisLine: {
                lineStyle: {
                    width: 12,
                    color: [
                        [0.3, '#22c55e'],
                        [0.6, '#f97316'],
                        [1, '#ef4444'],
                    ]
                }
            },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            detail: {
                formatter: `{value}`,
                rich: {
                    value: { fontSize: 18, fontWeight: 700, color, align: 'center' },
                },
                offsetCenter: [0, '60%'],
                fontSize: 18,
            },
            data: [{ value: probability, name: '风险概率' }],
        }]
    }, true);
    return chart;
}
