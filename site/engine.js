/* In-browser port of src/algorithms/dijkstra.py and astar.py, run on the
   Manhattan road network exported from data/manhattan_drive.graphml.
   Same heap ordering (priority, insertion counter), same haversine
   heuristic, same one-way edges, so the explored counts match the Python. */
(function (root) {
  "use strict";
  var D = root.MANHATTAN;
  var N = D.n.length / 2, E = D.e.length / 3;
  var LON = new Float64Array(N), LAT = new Float64Array(N);
  for (var i = 0; i < N; i++) {
    LON[i] = D.lon0 + D.n[2 * i] / 1e7;
    LAT[i] = D.lat0 + D.n[2 * i + 1] / 1e7;
  }

  // Adjacency in compressed rows, preserving each node's edge insertion order.
  var off = new Int32Array(N + 1);
  for (var k = 0; k < E; k++) off[D.e[3 * k] + 1]++;
  for (i = 0; i < N; i++) off[i + 1] += off[i];
  var to = new Int32Array(E), wt = new Float64Array(E), fill = off.slice(0, N);
  for (k = 0; k < E; k++) {
    var p = fill[D.e[3 * k]]++;
    to[p] = D.e[3 * k + 1];
    wt[p] = D.e[3 * k + 2] / 1000;
  }

  var R = 6371000, RAD = Math.PI / 180;
  function hav(a, b) {
    var p1 = LAT[a] * RAD, p2 = LAT[b] * RAD;
    var dp = (LAT[b] - LAT[a]) * RAD, dl = (LON[b] - LON[a]) * RAD;
    var s = Math.pow(Math.sin(dp / 2), 2) + Math.cos(p1) * Math.cos(p2) * Math.pow(Math.sin(dl / 2), 2);
    return 2 * R * Math.asin(Math.sqrt(s));
  }
  function havPoint(lat, lon, b) {
    var p1 = lat * RAD, p2 = LAT[b] * RAD;
    var dp = (LAT[b] - lat) * RAD, dl = (LON[b] - lon) * RAD;
    var s = Math.pow(Math.sin(dp / 2), 2) + Math.cos(p1) * Math.cos(p2) * Math.pow(Math.sin(dl / 2), 2);
    return 2 * R * Math.asin(Math.sqrt(s));
  }

  // Binary min-heap on (priority, counter), like Python's heapq with a tie-breaker.
  function Heap() { this.p = []; this.c = []; this.v = []; }
  Heap.prototype.less = function (i, j) {
    return this.p[i] < this.p[j] || (this.p[i] === this.p[j] && this.c[i] < this.c[j]);
  };
  Heap.prototype.swap = function (i, j) {
    var t = this.p[i]; this.p[i] = this.p[j]; this.p[j] = t;
    t = this.c[i]; this.c[i] = this.c[j]; this.c[j] = t;
    t = this.v[i]; this.v[i] = this.v[j]; this.v[j] = t;
  };
  Heap.prototype.push = function (pri, cnt, val) {
    var i = this.p.length;
    this.p.push(pri); this.c.push(cnt); this.v.push(val);
    while (i > 0) {
      var parent = (i - 1) >> 1;
      if (!this.less(i, parent)) break;
      this.swap(i, parent); i = parent;
    }
  };
  Heap.prototype.pop = function () {
    var top = [this.p[0], this.v[0]], last = this.p.length - 1;
    this.swap(0, last);
    this.p.pop(); this.c.pop(); this.v.pop();
    var n = this.p.length, i = 0;
    for (;;) {
      var l = 2 * i + 1, r = l + 1, m = i;
      if (l < n && this.less(l, m)) m = l;
      if (r < n && this.less(r, m)) m = r;
      if (m === i) break;
      this.swap(i, m); i = m;
    }
    return top;
  };

  function search(start, goal, useHeuristic) {
    var g = new Float64Array(N).fill(Infinity), prev = new Int32Array(N).fill(-1);
    var visited = new Uint8Array(N), order = [], heap = new Heap(), counter = 0;
    g[start] = 0;
    heap.push(useHeuristic ? hav(start, goal) : 0, counter++, start);
    while (heap.p.length) {
      var top = heap.pop(), node = top[1];
      if (visited[node]) continue;
      visited[node] = 1;
      order.push(node);
      if (node === goal) break;
      var base = useHeuristic ? g[node] : top[0];
      for (var q = off[node]; q < off[node + 1]; q++) {
        var nb = to[q];
        if (visited[nb]) continue;
        var nd = base + wt[q];
        if (nd < g[nb]) {
          g[nb] = nd; prev[nb] = node;
          heap.push(useHeuristic ? nd + hav(nb, goal) : nd, counter++, nb);
        }
      }
    }
    var found = visited[goal] === 1, path = [];
    if (found) {
      for (var n = goal; n !== -1; n = prev[n]) { path.push(n); if (n === start) break; }
      path.reverse();
    }
    return { order: order, path: path, cost: g[goal], found: found, explored: order.length };
  }

  function nearest(lat, lon) {
    var best = 0, bestD = Infinity;
    for (var i = 0; i < N; i++) {
      var d = havPoint(lat, lon, i);
      if (d < bestD) { bestD = d; best = i; }
    }
    return best;
  }

  root.RouteEngine = {
    N: N, E: E, LON: LON, LAT: LAT, off: off, to: to, edges: D.e,
    dist: hav, nearest: nearest,
    dijkstra: function (s, t) { return search(s, t, false); },
    astar: function (s, t) { return search(s, t, true); }
  };
})(typeof window !== "undefined" ? window : globalThis);
