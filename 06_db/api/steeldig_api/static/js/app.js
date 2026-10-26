/* 图表与交互：轻量封装，统一主题 */
(function () {
  const PALETTE = ['#2563eb', '#7c3aed', '#0e9384', '#d97706', '#db2777',
                   '#0891b2', '#65a30d', '#9333ea', '#dc2626', '#475569'];

  const BASE = {
    color: PALETTE,
    textStyle: { fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif',
                 color: '#344054' },
    grid: { left: 8, right: 14, top: 24, bottom: 6, containLabel: true },
    tooltip: {
      backgroundColor: 'rgba(16,24,40,.94)', borderWidth: 0,
      textStyle: { color: '#fff', fontSize: 12 },
      padding: [8, 10], extraCssText: 'border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.18)'
    },
  };

  window.sdChart = function (elId, option, opts) {
    const el = document.getElementById(elId);
    if (!el) return null;
    const chart = echarts.init(el, null, { renderer: 'svg' });
    chart.setOption(Object.assign({}, BASE, option, {
      tooltip: Object.assign({}, BASE.tooltip, option.tooltip || {}),
      grid: Object.assign({}, BASE.grid, option.grid || {})
    }));
    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(el);
    return chart;
  };

  window.sdAxis = function (extra) {
    return Object.assign({
      axisLine: { lineStyle: { color: '#e6e8ec' } },
      axisTick: { show: false },
      axisLabel: { color: '#667085', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f2f5' } }
    }, extra || {});
  };

  /* 侧边栏当前项高亮（服务端已处理，这里兜底） */
  document.querySelectorAll('.nav a').forEach(a => {
    if (a.getAttribute('href') === location.pathname) a.classList.add('active');
  });
})();
