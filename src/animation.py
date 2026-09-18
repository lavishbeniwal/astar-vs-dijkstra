"""Builds a self-contained HTML/JS component that replays the real order in
which each algorithm visited nodes, node by node, at a controllable speed --
so the search is watched happening rather than only shown as a finished map."""

import json
import math

from src.algorithms.common import SearchResult
from src.graph import Graph

# Dark theme, matched to the rest of the app.
CANVAS_BG = "#1E2A36"
EDGE_COLOR = "#3A4E5C"
BORDER_COLOR = "#2C3B48"
DIJKSTRA_LOW = "#4A3416"
DIJKSTRA_HIGH = "#F2A93B"
ASTAR_LOW = "#12332F"
ASTAR_HIGH = "#4FD1C5"
PATH_COLOR = "#6C8CFF"
START_COLOR = "#4ADE80"
GOAL_COLOR = "#F87171"
MARKER_LABEL_COLOR = "#E6EDF1"

CANVAS_SCALE = 2  # fixed retina-style backing-store multiplier, known at generation time (no runtime sizing)


def _route_bounds(graph: Graph, node_ids, pad_frac: float = 0.15) -> tuple:
    """Bounding box (in lon/lat) around only the nodes relevant to this
    search, so the canvas zooms to where the action is instead of showing
    the whole borough at a tiny scale."""
    lons = [graph.positions[n][0] for n in node_ids]
    lats = [graph.positions[n][1] for n in node_ids]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    lon_pad = (max_lon - min_lon) * pad_frac or 0.002
    lat_pad = (max_lat - min_lat) * pad_frac or 0.002
    return (min_lon - lon_pad, max_lon + lon_pad, min_lat - lat_pad, max_lat + lat_pad)


def _panel_dimensions(bounds: tuple, max_width: int = 440, max_height: int = 540) -> tuple:
    min_lon, max_lon, min_lat, max_lat = bounds
    mean_lat = (min_lat + max_lat) / 2
    aspect = 1 / math.cos(math.radians(mean_lat))
    geo_w = (max_lon - min_lon) * aspect or 1e-9
    geo_h = (max_lat - min_lat) or 1e-9

    height = max_height
    width = height * (geo_w / geo_h)
    if width > max_width:
        width = max_width
        height = width * (geo_h / geo_w)
    return round(width), round(height)


def _project_positions(graph: Graph, bounds: tuple, width: float, height: float, pad: float = 20.0) -> dict:
    min_lon, max_lon, min_lat, max_lat = bounds
    mean_lat = (min_lat + max_lat) / 2
    aspect = 1 / math.cos(math.radians(mean_lat))
    geo_w = (max_lon - min_lon) * aspect or 1e-9
    geo_h = (max_lat - min_lat) or 1e-9
    scale = min((width - 2 * pad) / geo_w, (height - 2 * pad) / geo_h)

    positions = {}
    for node, (lon, lat) in graph.positions.items():
        x = pad + (lon - min_lon) * aspect * scale
        y = pad + (max_lat - lat) * scale
        positions[node] = [round(x, 1), round(y, 1)]
    return positions


def _dedup_edge_segments(graph: Graph, pixel_pos: dict, bounds_px: tuple, margin: float = 40.0) -> list:
    """Only keep edges that could plausibly be visible, so we're not paying
    to draw thousands of segments far outside the cropped view."""
    min_x, min_y, max_x, max_y = bounds_px
    seen = set()
    segments = []
    for node, edges in graph.adjacency.items():
        x1, y1 = pixel_pos[node]
        if x1 < min_x - margin or x1 > max_x + margin or y1 < min_y - margin or y1 > max_y + margin:
            near_a = False
        else:
            near_a = True
        for neighbor, _ in edges:
            key = frozenset((node, neighbor))
            if key in seen:
                continue
            x2, y2 = pixel_pos[neighbor]
            near_b = not (x2 < min_x - margin or x2 > max_x + margin or y2 < min_y - margin or y2 > max_y + margin)
            if not (near_a or near_b):
                continue
            seen.add(key)
            segments.append([x1, y1, x2, y2])
    return segments


def build_animation_html(
    graph: Graph,
    start,
    goal,
    dijkstra_result: SearchResult,
    astar_result: SearchResult,
    default_speed: int = 400,
) -> str:
    """Returns HTML for two canvases that replay dijkstra_result.explored_order
    and astar_result.explored_order node by node, at `default_speed`
    nodes/second, adjustable and restartable. The view is cropped to the
    area actually touched by either search."""
    relevant_nodes = set(dijkstra_result.explored_order) | set(astar_result.explored_order) | {start, goal}
    bounds = _route_bounds(graph, relevant_nodes)
    panel_width, panel_height = _panel_dimensions(bounds)

    pixel_pos = _project_positions(graph, bounds, panel_width, panel_height)
    edge_segments = _dedup_edge_segments(graph, pixel_pos, (0, 0, panel_width, panel_height))

    data = {
        "width": panel_width,
        "height": panel_height,
        "edges": edge_segments,
        "dijkstra": {
            "points": [pixel_pos[n] for n in dijkstra_result.explored_order],
            "path": [pixel_pos[n] for n in dijkstra_result.path],
        },
        "astar": {
            "points": [pixel_pos[n] for n in astar_result.explored_order],
            "path": [pixel_pos[n] for n in astar_result.path],
        },
        "start": pixel_pos[start],
        "goal": pixel_pos[goal],
        "defaultSpeed": default_speed,
        "scale": CANVAS_SCALE,
    }

    bitmap_w, bitmap_h = panel_width * CANVAS_SCALE, panel_height * CANVAS_SCALE

    return _TEMPLATE.format(
        data_json=json.dumps(data),
        panel_width=panel_width,
        panel_height=panel_height,
        bitmap_w=bitmap_w,
        bitmap_h=bitmap_h,
        canvas_bg=CANVAS_BG,
        border_color=BORDER_COLOR,
        edge_color=EDGE_COLOR,
        dijkstra_high=DIJKSTRA_HIGH,
        astar_high=ASTAR_HIGH,
        dijkstra_low=DIJKSTRA_LOW,
        astar_low=ASTAR_LOW,
        path_color=PATH_COLOR,
        start_color=START_COLOR,
        goal_color=GOAL_COLOR,
        marker_label_color=MARKER_LABEL_COLOR,
    )


_TEMPLATE = """
<div id="sim-root" style="font-family:'IBM Plex Sans',system-ui,sans-serif;">
  <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:12px;">
    <button id="sim-play" style="font-family:inherit; font-weight:600; font-size:13px; padding:7px 16px;
      border-radius:6px; border:none; background:{path_color}; color:#0B1017; cursor:pointer;
      transition:filter 0.15s ease;">Pause</button>
    <button id="sim-restart" class="sim-btn-secondary" style="font-family:inherit; font-weight:600; font-size:13px;
      padding:7px 16px; border-radius:6px; border:1px solid {border_color}; background:transparent;
      color:#E6EDF1; cursor:pointer; transition:background 0.15s ease;">Restart</button>
    <button id="sim-skip" class="sim-btn-secondary" style="font-family:inherit; font-weight:600; font-size:13px;
      padding:7px 16px; border-radius:6px; border:1px solid {border_color}; background:transparent;
      color:#E6EDF1; cursor:pointer; transition:background 0.15s ease;">Skip to end</button>
    <label style="font-size:12px; color:#90A2AD; display:flex; align-items:center; gap:6px; margin-left:6px;">
      Speed
      <input id="sim-speed" type="range" min="100" max="4000" step="100" style="vertical-align:middle;">
      <span id="sim-speed-label" style="font-family:'IBM Plex Mono',monospace; width:78px; display:inline-block;"></span>
    </label>
  </div>
  <style>
    .sim-btn-secondary:hover {{ background:rgba(230,237,241,0.08) !important; }}
  </style>
  <div style="display:flex; gap:16px; flex-wrap:wrap; justify-content:center;">
    <div style="width:{panel_width}px; max-width:100%;">
      <div style="font-weight:600; font-size:13px; color:{dijkstra_high}; margin-bottom:6px;">
        Dijkstra (Uniform Cost Search) &mdash; <span id="d-count" style="font-family:'IBM Plex Mono',monospace;">0</span> /
        <span id="d-total" style="font-family:'IBM Plex Mono',monospace;">0</span> nodes visited
      </div>
      <canvas id="canvas-dijkstra" width="{bitmap_w}" height="{bitmap_h}"
        style="width:{panel_width}px; height:{panel_height}px; border-radius:10px; background:{canvas_bg};
        border:1px solid {border_color}; display:block;"></canvas>
    </div>
    <div style="width:{panel_width}px; max-width:100%;">
      <div style="font-weight:600; font-size:13px; color:{astar_high}; margin-bottom:6px;">
        A* Search &mdash; <span id="a-count" style="font-family:'IBM Plex Mono',monospace;">0</span> /
        <span id="a-total" style="font-family:'IBM Plex Mono',monospace;">0</span> nodes visited
      </div>
      <canvas id="canvas-astar" width="{bitmap_w}" height="{bitmap_h}"
        style="width:{panel_width}px; height:{panel_height}px; border-radius:10px; background:{canvas_bg};
        border:1px solid {border_color}; display:block;"></canvas>
    </div>
  </div>
</div>
<script>
(function() {{
  const DATA = {data_json};
  const EDGE_COLOR = "{edge_color}";
  const PATH_COLOR = "{path_color}";
  const START_COLOR = "{start_color}";
  const GOAL_COLOR = "{goal_color}";
  const CANVAS_BG = "{canvas_bg}";
  const LABEL_COLOR = "{marker_label_color}";

  const panels = [
    {{ canvasId: "canvas-dijkstra", countId: "d-count", totalId: "d-total",
       colorLow: "{dijkstra_low}", colorHigh: "{dijkstra_high}", data: DATA.dijkstra }},
    {{ canvasId: "canvas-astar", countId: "a-count", totalId: "a-total",
       colorLow: "{astar_low}", colorHigh: "{astar_high}", data: DATA.astar }},
  ];

  function lerpColor(hexA, hexB, t) {{
    const a = [1,3,5].map(i => parseInt(hexA.substr(i,2), 16));
    const b = [1,3,5].map(i => parseInt(hexB.substr(i,2), 16));
    const c = a.map((v,i) => Math.round(v + (b[i]-v)*t));
    return `rgb(${{c[0]}},${{c[1]}},${{c[2]}})`;
  }}

  function setupCanvas(canvas) {{
    const ctx = canvas.getContext("2d");
    ctx.scale(DATA.scale, DATA.scale);
    return ctx;
  }}

  function drawEdges(ctx) {{
    ctx.strokeStyle = EDGE_COLOR;
    ctx.lineWidth = 0.7;
    ctx.beginPath();
    for (const [x1,y1,x2,y2] of DATA.edges) {{
      ctx.moveTo(x1,y1);
      ctx.lineTo(x2,y2);
    }}
    ctx.stroke();
  }}

  function drawMarker(ctx, pos, color, radius, label) {{
    ctx.beginPath();
    ctx.arc(pos[0], pos[1], radius, 0, Math.PI*2);
    ctx.fillStyle = CANVAS_BG;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = color;
    ctx.stroke();
    if (label) {{
      ctx.fillStyle = LABEL_COLOR;
      ctx.font = "bold 9px 'IBM Plex Mono', monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(label, pos[0], pos[1]+1);
    }}
  }}

  function drawPath(ctx, points) {{
    if (points.length < 2) return;
    ctx.save();
    ctx.filter = "blur(3px)";
    ctx.globalAlpha = 0.6;
    ctx.strokeStyle = PATH_COLOR;
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]);
    for (const p of points.slice(1)) ctx.lineTo(p[0], p[1]);
    ctx.stroke();
    ctx.restore();

    ctx.strokeStyle = PATH_COLOR;
    ctx.lineWidth = 2.6;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]);
    for (const p of points.slice(1)) ctx.lineTo(p[0], p[1]);
    ctx.stroke();
  }}

  for (const panel of panels) {{
    const canvas = document.getElementById(panel.canvasId);
    panel.ctx = setupCanvas(canvas);
    drawEdges(panel.ctx);
    document.getElementById(panel.totalId).textContent = panel.data.points.length;
    panel.index = 0;
    panel.pathDrawn = false;
  }}

  let playing = true;
  let lastTime = null;
  let speed = DATA.defaultSpeed;

  const speedInput = document.getElementById("sim-speed");
  const speedLabel = document.getElementById("sim-speed-label");
  speedInput.value = speed;
  speedLabel.textContent = speed + " nodes/s";
  speedInput.addEventListener("input", () => {{
    speed = parseInt(speedInput.value, 10);
    speedLabel.textContent = speed + " nodes/s";
  }});

  function revealUpTo(panel, targetIndex) {{
    const pts = panel.data.points;
    const n = pts.length || 1;
    while (panel.index < targetIndex && panel.index < pts.length) {{
      const t = panel.index / n;
      panel.ctx.beginPath();
      panel.ctx.arc(pts[panel.index][0], pts[panel.index][1], 2.8, 0, Math.PI*2);
      panel.ctx.fillStyle = lerpColor(panel.colorLow, panel.colorHigh, t);
      panel.ctx.fill();
      panel.index++;
    }}
    document.getElementById(panel.countId).textContent = panel.index;
    if (panel.index >= pts.length && !panel.pathDrawn) {{
      drawMarker(panel.ctx, DATA.start, START_COLOR, 6, "A");
      drawMarker(panel.ctx, DATA.goal, GOAL_COLOR, 6, "B");
      drawPath(panel.ctx, panel.data.path);
      panel.pathDrawn = true;
    }}
  }}

  function allDone() {{
    return panels.every(p => p.index >= p.data.points.length);
  }}

  function frame(t) {{
    if (lastTime === null) lastTime = t;
    const dt = Math.min((t - lastTime) / 1000, 0.05); // cap so a throttled/backgrounded tab
    lastTime = t;                                      // resumes smoothly instead of jumping to the end
    if (playing && !allDone()) {{
      const toAdvance = Math.max(1, Math.round(speed * dt));
      for (const panel of panels) {{
        revealUpTo(panel, panel.index + toAdvance);
      }}
    }}
    requestAnimationFrame(frame);
  }}
  requestAnimationFrame(frame);

  document.getElementById("sim-play").addEventListener("click", (e) => {{
    playing = !playing;
    e.target.textContent = playing ? "Pause" : "Play";
  }});

  document.getElementById("sim-restart").addEventListener("click", () => {{
    for (const panel of panels) {{
      panel.ctx.clearRect(0, 0, DATA.width, DATA.height);
      drawEdges(panel.ctx);
      panel.index = 0;
      panel.pathDrawn = false;
      document.getElementById(panel.countId).textContent = 0;
    }}
    lastTime = null;
    playing = true;
    document.getElementById("sim-play").textContent = "Pause";
  }});

  document.getElementById("sim-skip").addEventListener("click", () => {{
    for (const panel of panels) revealUpTo(panel, panel.data.points.length);
    playing = false;
    document.getElementById("sim-play").textContent = "Play";
  }});
}})();
</script>
"""
