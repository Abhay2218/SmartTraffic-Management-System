// ============================================================================
// SmartTraffic Analytics & OS Synchronization Dashboard Module
// ============================================================================

const AnalyticsApp = {
  wtChart: null,
  throughputChart: null,

  init() {
    this.initCharts();
    this.runBenchmark();
    this.bindEvents();
  },

  initCharts() {
    const ctxWt = document.getElementById('chart-waiting-time')?.getContext('2d');
    if (ctxWt) {
      this.wtChart = new Chart(ctxWt, {
        type: 'bar',
        data: {
          labels: ['FCFS', 'Priority (Aging)', 'Round Robin', 'Adaptive (OS Dynamic)'],
          datasets: [
            {
              label: 'Avg Waiting Time (sec)',
              data: [0, 0, 0, 0],
              backgroundColor: 'rgba(37, 99, 235, 0.75)',
              borderColor: '#2563eb',
              borderWidth: 1,
            },
            {
              label: 'Avg Turnaround Time (sec)',
              data: [0, 0, 0, 0],
              backgroundColor: 'rgba(16, 185, 129, 0.75)',
              borderColor: '#10b981',
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true, title: { display: true, text: 'Seconds' } },
          },
        },
      });
    }

    const ctxTp = document.getElementById('chart-throughput')?.getContext('2d');
    if (ctxTp) {
      this.throughputChart = new Chart(ctxTp, {
        type: 'bar',
        data: {
          labels: ['FCFS', 'Priority (Aging)', 'Round Robin', 'Adaptive (OS Dynamic)'],
          datasets: [
            {
              label: 'Throughput (veh/sec)',
              data: [0, 0, 0, 0],
              backgroundColor: 'rgba(245, 158, 11, 0.75)',
              borderColor: '#f59e0b',
              borderWidth: 1,
              yAxisID: 'y',
            },
            {
              label: 'Emergency Response Wait (sec)',
              data: [0, 0, 0, 0],
              backgroundColor: 'rgba(239, 68, 68, 0.75)',
              borderColor: '#ef4444',
              borderWidth: 1,
              yAxisID: 'y1',
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              type: 'linear',
              display: true,
              position: 'left',
              beginAtZero: true,
              title: { display: true, text: 'Throughput (veh/sec)' },
            },
            y1: {
              type: 'linear',
              display: true,
              position: 'right',
              beginAtZero: true,
              grid: { drawOnChartArea: false },
              title: { display: true, text: 'Emergency Wait (sec)' },
            },
          },
        },
      });
    }
  },

  async runBenchmark() {
    try {
      const quantum = parseInt(document.getElementById('input-quantum')?.value, 10) || 2;
      const resp = await Api.getAnalyticsBenchmark(SimulationApp.currentSimId, quantum);
      if (resp && resp.comparison) {
        this.updateCharts(resp.comparison);
        this.updateTable(resp.comparison);
      }
    } catch (err) {
      console.warn("Benchmark error:", err);
    }
  },

  updateCharts(comp) {
    const algs = ['FCFS', 'PRIORITY', 'ROUND_ROBIN', 'ADAPTIVE'];
    const avgWts = algs.map((a) => (comp[a] ? comp[a].avg_waiting_time : 0));
    const avgTats = algs.map((a) => (comp[a] ? comp[a].avg_turnaround_time : 0));
    const tps = algs.map((a) => (comp[a] ? comp[a].throughput : 0));
    const emergWts = algs.map((a) => (comp[a] ? comp[a].avg_emergency_wait : 0));

    if (this.wtChart) {
      this.wtChart.data.datasets[0].data = avgWts;
      this.wtChart.data.datasets[1].data = avgTats;
      this.wtChart.update();
    }

    if (this.throughputChart) {
      this.throughputChart.data.datasets[0].data = tps;
      this.throughputChart.data.datasets[1].data = emergWts;
      this.throughputChart.update();
    }
  },

  updateTable(comp) {
    const tbody = document.getElementById('benchmark-table-body');
    if (!tbody) return;

    const algs = [
      { key: 'FCFS', name: 'First-Come First-Served' },
      { key: 'PRIORITY', name: 'Priority with Aging' },
      { key: 'ROUND_ROBIN', name: 'Round Robin' },
      { key: 'ADAPTIVE', name: 'Adaptive Dynamic Scheduling' },
    ];

    tbody.innerHTML = algs.map(({ key, name }) => {
      const d = comp[key] || {};
      const isBestEmerg = key === 'ADAPTIVE' || key === 'PRIORITY';
      return `
        <tr>
          <td><b>${name}</b></td>
          <td>${(d.avg_waiting_time || 0).toFixed(2)}s</td>
          <td>${(d.avg_turnaround_time || 0).toFixed(2)}s</td>
          <td>${(d.throughput || 0).toFixed(3)} veh/s</td>
          <td>${d.total_time || 0}s</td>
          <td>
            <span class="badge ${isBestEmerg ? 'badge-completed' : 'badge-waiting'}">
              ${(d.avg_emergency_wait || 0).toFixed(2)}s
            </span>
          </td>
          <td style="font-family: monospace; font-size: 0.75rem;">
            [${(d.execution_order || []).slice(0, 8).join(', ')}${(d.execution_order || []).length > 8 ? '...' : ''}]
          </td>
        </tr>
      `;
    }).join('');
  },

  async runSyncVerification() {
    const btn = document.getElementById('btn-run-sync-test');
    const term = document.getElementById('sync-terminal-output');
    if (btn) btn.disabled = true;
    if (term) term.innerHTML = "Invoking compiled C OS Engine (--test-sync)...\nWaiting on Windows Mutex & Semaphore...";

    try {
      const resp = await Api.runSyncTest();
      if (resp && resp.data) {
        const d = resp.data;
        let html = `
          <div style="margin-bottom: 8px;">
            <span class="sync-metric-pill">Status: ${d.test_passed ? 'PASS (100%)' : 'FAIL'}</span>
            <span class="sync-metric-pill">Mutex Locks: ${d.mutex_locks_acquired}</span>
            <span class="sync-metric-pill">Semaphore Waits: ${d.semaphore_waits_completed}</span>
            <span class="sync-metric-pill">Collisions Prevented: ${d.race_conditions_prevented}</span>
          </div>
          <div>${(d.logs || []).map((l) => `&gt; ${l}`).join('<br>')}</div>
        `;
        if (term) term.innerHTML = html;
      }
    } catch (err) {
      if (term) term.innerHTML = `<span style="color: #ef4444;">Sync Error: ${err.message}</span>`;
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  bindEvents() {
    document.getElementById('btn-run-benchmark')?.addEventListener('click', () => this.runBenchmark());
    document.getElementById('btn-run-sync-test')?.addEventListener('click', () => this.runSyncVerification());
  },
};
