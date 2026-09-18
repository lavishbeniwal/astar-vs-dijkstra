"""Interactive demo: pick a start and destination in Manhattan, watch Dijkstra
and A* search node by node in real time, and compare their routes and search
behavior side by side.

Run with:

    streamlit run app.py
"""

import folium
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium

from src.animation import build_animation_html
from src.graph_builder import build_road_graph, nearest_node
from src.metrics import compare
from src.visualize import plot_comparison

st.set_page_config(page_title="A* vs Dijkstra: Smart Route Planner", page_icon="🧭", layout="wide")

MAP_CENTER = (40.7549, -73.9840)

NAMED_LOCATIONS = {
    "Battery Park": (40.7033, -74.0170),
    "Financial District (Wall St)": (40.7074, -74.0113),
    "West Village (8th Ave & W 14th St)": (40.7402, -74.0027),
    "Union Square": (40.7359, -73.9911),
    "Chelsea Market": (40.7424, -74.0061),
    "Grand Central Terminal": (40.7527, -73.9772),
    "Times Square": (40.7580, -73.9855),
    "Bryant Park": (40.7536, -73.9832),
    "Upper East Side (86th St & 5th Ave)": (40.7825, -73.9601),
    "Upper West Side (86th St & CPW)": (40.7850, -73.9713),
    "Harlem (125th St)": (40.8075, -73.9465),
    "Inwood": (40.8677, -73.9212),
}

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --bg: #0E151C;
  --surface: #16202A;
  --surface-2: #1E2A36;
  --border: #2C3B48;
  --ink: #E6EDF1;
  --ink-muted: #90A2AD;
  --dijkstra: #F2A93B;
  --astar: #4FD1C5;
  --accent: #6C8CFF;
}

html, body, [class*="css"], .stMarkdown, .stSelectbox label, .stRadio label { font-family: 'IBM Plex Sans', sans-serif; }
h1, h2, h3 { font-family: 'Big Shoulders Display', sans-serif !important; text-transform: uppercase; letter-spacing: 0.01em; }

@keyframes fadeInUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.app-eyebrow, .headline-card, .metrics-table, [data-testid="stExpander"] { animation: fadeInUp 0.45s ease both; }

.app-eyebrow { font-family:'IBM Plex Mono',monospace; font-size:0.72rem; font-weight:600; letter-spacing:0.12em;
  text-transform:uppercase; color:var(--ink-muted); margin-bottom:0.2rem; }
.app-caption { color:var(--ink-muted); font-size:0.95rem; margin-top:-0.4rem; }

.headline-card { background: linear-gradient(135deg, rgba(79,209,197,0.14), rgba(108,140,255,0.08));
  border:1px solid var(--border); border-radius:14px; padding:1.15rem 1.4rem; margin: 0.6rem 0 1.1rem; }
.headline-card .big { font-family:'IBM Plex Mono',monospace; font-size:2.1rem; font-weight:600; color:var(--astar);
  line-height:1; }
.headline-card .sub { color:var(--ink); font-size:0.95rem; margin-top:0.4rem; opacity:0.9; }

.metrics-table { width:100%; border-collapse:collapse; font-family:'IBM Plex Sans',sans-serif; }
.metrics-table th { text-align:left; font-family:'IBM Plex Mono',monospace; text-transform:uppercase; font-size:0.68rem;
  letter-spacing:0.06em; color:var(--ink-muted); font-weight:600; padding:0.5rem 0.7rem; border-bottom:1px solid var(--border); }
.metrics-table td { padding:0.6rem 0.7rem; border-bottom:1px solid var(--border); font-size:0.92rem;
  font-variant-numeric: tabular-nums; color:var(--ink); transition:background 0.15s ease; }
.metrics-table tr:hover td { background: rgba(230,237,241,0.04); }
.metrics-table td.winner { font-weight:700; }
.metrics-table td.dijkstra-cell.winner { color:var(--dijkstra); }
.metrics-table td.astar-cell.winner { color:var(--astar); }
.win-tag { font-family:'IBM Plex Mono',monospace; font-size:0.64rem; font-weight:600; padding:0.12rem 0.42rem;
  border-radius:4px; margin-left:0.5rem; white-space:nowrap; }
.win-tag.win { background: rgba(79,209,197,0.18); color:var(--astar); }
.win-tag.tie { background: rgba(144,162,173,0.15); color:var(--ink-muted); }

div[data-testid="stButton"] button { transition: transform 0.12s ease, filter 0.12s ease; }
div[data-testid="stButton"] button:hover { transform: translateY(-1px); filter: brightness(1.1); }

/* Segmented-pill radio for the start/destination picker mode */
div[data-testid="stRadio"] > div[role="radiogroup"] {
  display:flex; gap:4px; background:var(--surface-2); padding:4px; border-radius:10px; width:fit-content;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] {
  margin:0; padding:8px 18px; border-radius:8px; cursor:pointer; transition:background 0.15s ease;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child { display:none !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"] p { margin:0; font-size:0.88rem; font-weight:500; color:var(--ink-muted); transition:color 0.15s ease; }
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover { background: rgba(230,237,241,0.07); }
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) { background:var(--accent); }
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p { color:#0B1017; font-weight:600; }

/* Selects */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  border-radius: 8px !important;
  border-color: var(--border) !important;
  transition: border-color 0.15s ease, box-shadow 0.2s ease;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within > div {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(108,140,255,0.25);
}

.section-label { font-family:'Big Shoulders Display',sans-serif; text-transform:uppercase; letter-spacing:0.02em;
  font-size:1.1rem; color:var(--ink); margin: 0 0 0.6rem; }

/* Staggered reveal for comparison rows */
.metrics-table tbody tr { animation: fadeInUp 0.4s ease both; }
.metrics-table tbody tr:nth-child(1) { animation-delay: 0.05s; }
.metrics-table tbody tr:nth-child(2) { animation-delay: 0.12s; }
.metrics-table tbody tr:nth-child(3) { animation-delay: 0.19s; }
.metrics-table tbody tr:nth-child(4) { animation-delay: 0.26s; }
</style>
"""


@st.cache_resource(show_spinner="Loading Manhattan's road network (first run downloads it, ~1 minute)...")
def get_graph():
    return build_road_graph()


def init_state() -> None:
    st.session_state.setdefault("start_coord", None)
    st.session_state.setdefault("goal_coord", None)
    st.session_state.setdefault("_last_click", None)


def render_picker(graph) -> None:
    st.markdown('<div class="section-label">Choose a route</div>', unsafe_allow_html=True)
    mode = st.radio(
        "Choose start and destination by:",
        ["Picking from a list", "Clicking on the map"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if st.session_state.get("_mode") != mode:
        st.session_state.start_coord = None
        st.session_state.goal_coord = None
        st.session_state._last_click = None
        st.session_state._mode = mode

    if mode == "Picking from a list":
        labels = list(NAMED_LOCATIONS.keys())
        col1, col2 = st.columns(2)
        start_label = col1.selectbox("From", labels, index=labels.index("West Village (8th Ave & W 14th St)"))
        goal_label = col2.selectbox("To", labels, index=labels.index("Grand Central Terminal"))
        st.session_state.start_coord = NAMED_LOCATIONS[start_label]
        st.session_state.goal_coord = NAMED_LOCATIONS[goal_label]
        return

    st.caption("Click once to set the start, click again to set the destination. Click a third time to start over.")
    m = folium.Map(location=MAP_CENTER, zoom_start=12, tiles="cartodbpositron")
    if st.session_state.start_coord:
        folium.Marker(st.session_state.start_coord, tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
    if st.session_state.goal_coord:
        folium.Marker(st.session_state.goal_coord, tooltip="Destination", icon=folium.Icon(color="red")).add_to(m)

    map_data = st_folium(m, height=480, width=None, key="click_map")

    if map_data and map_data.get("last_clicked"):
        click = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])
        if click != st.session_state._last_click:
            st.session_state._last_click = click
            if st.session_state.start_coord is None:
                st.session_state.start_coord = click
            elif st.session_state.goal_coord is None:
                st.session_state.goal_coord = click
            else:
                st.session_state.start_coord = click
                st.session_state.goal_coord = None
            st.rerun()

    if st.button("Reset points"):
        st.session_state.start_coord = None
        st.session_state.goal_coord = None
        st.session_state._last_click = None
        st.rerun()


def _row(label: str, d_val: str, a_val: str, winner: str) -> str:
    d_class = "winner" if winner == "dijkstra" else ""
    a_class = "winner" if winner == "astar" else ""
    d_tag = '<span class="win-tag win">faster</span>' if winner == "dijkstra" else ""
    a_tag = '<span class="win-tag win">faster</span>' if winner == "astar" else ""
    if winner == "tie":
        d_tag = a_tag = '<span class="win-tag tie">tied</span>'
    return (
        f"<tr><td>{label}</td>"
        f'<td class="dijkstra-cell {d_class}">{d_val}{d_tag}</td>'
        f'<td class="astar-cell {a_class}">{a_val}{a_tag}</td></tr>'
    )


def render_metrics_table(d, a, graph) -> str:
    eff_d = d.nodes_explored / len(graph) * 100
    eff_a = a.nodes_explored / len(graph) * 100

    def winner(x, y):
        if abs(x - y) < 1e-9:
            return "tie"
        return "dijkstra" if x < y else "astar"

    rows = [
        _row("Route distance (km)", f"{d.cost / 1000:.2f}", f"{a.cost / 1000:.2f}", "tie"),
        _row("Nodes explored", f"{d.nodes_explored:,}", f"{a.nodes_explored:,}", winner(d.nodes_explored, a.nodes_explored)),
        _row(
            "Execution time (ms)",
            f"{d.execution_time * 1000:.2f}",
            f"{a.execution_time * 1000:.2f}",
            winner(d.execution_time, a.execution_time),
        ),
        _row("Search efficiency (% of graph touched)", f"{eff_d:.1f}%", f"{eff_a:.1f}%", winner(eff_d, eff_a)),
    ]
    return (
        '<table class="metrics-table"><thead><tr><th>Metric</th><th>Dijkstra</th><th>A*</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def render_comparison(graph, start_coord, goal_coord) -> None:
    with st.spinner("Running Dijkstra and A*..."):
        start = nearest_node(graph, *start_coord)
        goal = nearest_node(graph, *goal_coord)
        result = compare(graph, start, goal)

    d, a = result.dijkstra, result.astar

    if not (d.found and a.found):
        st.error("No route found between those two points.")
        return

    reduction = result.nodes_explored_reduction_pct
    st.markdown(
        f"""<div class="headline-card">
              <div class="big">{reduction:.0f}% fewer intersections</div>
              <div class="sub">A* found the identical optimal route ({d.cost / 1000:.2f} km) while considering
              {a.nodes_explored:,} intersections instead of Dijkstra's {d.nodes_explored:,} &mdash;
              {d.execution_time / a.execution_time:.1f}&times; less searching for the same answer.</div>
            </div>""",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.subheader("Watch the search")
        st.caption(
            "Every dot is a real intersection the algorithm actually visited, replayed in the exact order it "
            "happened. Dijkstra spreads outward in every direction; A* is pulled toward the destination."
        )
        animation_html = build_animation_html(graph, start, goal, d, a)
        components.html(animation_html, height=680, scrolling=True)

    with st.container(border=True):
        st.subheader("Comparison")
        st.markdown(render_metrics_table(d, a, graph), unsafe_allow_html=True)

    with st.expander("Static comparison map (for reports)"):
        fig = plot_comparison(graph, start, goal, d, a)
        st.pyplot(fig, width="stretch")
        import matplotlib.pyplot as plt

        plt.close(fig)


def main() -> None:
    init_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    graph = get_graph()

    st.markdown('<div class="app-eyebrow">AI Route Planning &middot; Search Algorithm Comparison</div>', unsafe_allow_html=True)
    st.title("A* vs Dijkstra: Smart Route Planner")
    st.markdown(
        f'<p class="app-caption">Manhattan drivable road network from OpenStreetMap &mdash; '
        f'{len(graph)} intersections, {sum(len(e) for e in graph.adjacency.values())} road segments.</p>',
        unsafe_allow_html=True,
    )
    st.write(
        "Pick a start and a destination, then run both search algorithms on the same real street network. "
        "Dijkstra expands by distance traveled alone; A* also uses a straight-line estimate to the destination."
    )

    with st.container(border=True):
        render_picker(graph)
        if st.session_state.start_coord and st.session_state.goal_coord:
            run_clicked = st.button("Run Comparison", type="primary")
        else:
            st.info("Pick both a start and a destination above to run the comparison.")
            run_clicked = False

    if run_clicked:
        render_comparison(graph, st.session_state.start_coord, st.session_state.goal_coord)


if __name__ == "__main__":
    main()
