import os
import streamlit as st
import requests
from collections import deque
from streamlit_agraph import agraph, Node, Edge, Config

# =============================================================================
# CONFIGURATION
# =============================================================================
API_URL = os.getenv("API_URL", "http://localhost:8000/v1")

# Color scheme
COLORS = {
    "start_node": "#FFFF00",    # Yellow - starting point
    "document": "#97C2FC",       # Blue - documents
    "entity": "#FB7E81",         # Red - entities
    "attribute": "#9C9C9C",      # Grey - attributes
    "edge_default": "#CCCCCC",
    "edge_mentions": "#FB7E81",
    "edge_related": "#97C2FC",
    "highlight": "#F7A7A6",
}


def api_request(method: str, endpoint: str, **kwargs):
    """Make API request with error handling. Returns (success, data_or_error)."""
    try:
        url = f"{API_URL}{endpoint}"
        if method == "GET":
            res = requests.get(url, params=kwargs.get("params"))
        else:
            res = requests.post(url, json=kwargs.get("json"))
        
        if res.status_code == 200:
            return True, res.json()
        return False, res.text
    except Exception as e:
        return False, f"Connection Error: {e}"


def get_node_label(node_data: dict, max_length: int = 30) -> str:
    """Extract display label from node data."""
    base = (
        node_data.get("title") or 
        node_data.get("name") or 
        node_data.get("text", "Node")
    )
    return (base[:max_length] + "…") if len(base) > max_length else base


def get_node_color(node_data: dict, start_id: str = None) -> str:
    """Determine node color based on type."""
    nid = node_data.get("id")
    if nid == start_id:
        return COLORS["start_node"]
    
    labels = node_data.get("labels", [])
    ntype = node_data.get("type")
    
    if "Entity" in labels or ntype == "Entity":
        return COLORS["entity"]
    if "Attribute" in labels or "Value" in labels or ntype in ("Attribute", "Value"):
        return COLORS["attribute"]
    return COLORS["document"]


def get_edge_color(edge_type: str) -> str:
    """Determine edge color based on type."""
    if edge_type == "MENTIONS":
        return COLORS["edge_mentions"]
    if edge_type in ("RELATED_TO", "SEMANTIC_NEAR"):
        return COLORS["edge_related"]
    return COLORS["edge_default"]


def build_graph_objects(nodes_data: list, edges_data: list, start_id: str = None, 
                        node_size: int = 15, show_all_edge_labels: bool = True) -> tuple:
    """Build Node and Edge objects for agraph visualization."""
    nodes = [
        Node(
            id=n["id"],
            label=get_node_label(n),
            color=get_node_color(n, start_id),
            size=node_size
        )
        for n in nodes_data
    ]
    
    edges = []
    for e in edges_data:
        # Show edge labels only around start node if configured
        label = e["type"] if show_all_edge_labels or e["source"] == start_id or e["target"] == start_id else None
        edges.append(Edge(
            source=e["source"],
            target=e["target"],
            label=label,
            color=get_edge_color(e["type"])
        ))
    
    return nodes, edges


def build_adjacency(edges_data: list) -> dict:
    """Build adjacency list from edge data."""
    adj = {}
    for e in edges_data:
        s, t = e.get("source"), e.get("target")
        if s and t:
            adj.setdefault(s, []).append(t)
            adj.setdefault(t, []).append(s)
    return adj


def compute_bfs_levels(start_id: str, adjacency: dict) -> dict:
    """Compute BFS levels from start node."""
    levels = {start_id: 0}
    queue = deque([start_id])
    while queue:
        current = queue.popleft()
        for nbr in adjacency.get(current, []):
            if nbr not in levels:
                levels[nbr] = levels[current] + 1
                queue.append(nbr)
    return levels


def render_graph(nodes: list, edges: list, width: int = 1000, height: int = 800, 
                 collapsible: bool = False):
    """Render graph with standard configuration."""
    config = Config(
        width=width,
        height=height,
        directed=True,
        nodeHighlightBehavior=True,
        highlightColor=COLORS["highlight"],
        collapsible=collapsible,
        node={"labelPosition": "top"},
        link={"renderLabel": True},
        d3={"gravity": -250, "linkLength": 140},
    )
    agraph(nodes=nodes, edges=edges, config=config)


def display_nodes_by_level(nodes: list, levels: dict):
    """Display nodes organized by BFS level."""
    level_buckets = {}
    for node in nodes:
        lvl = levels.get(node.id, -1)
        level_buckets.setdefault(lvl, []).append(node)
    
    st.subheader("📌 Found Nodes (Level-wise)")
    for lvl in sorted(level_buckets.keys()):
        st.markdown(f"### Level {lvl}")
        for node in level_buckets[lvl]:
            indent = "&nbsp;" * (lvl * 8)
            st.markdown(f"{indent}- **{node.label}** (`{node.id}`)", unsafe_allow_html=True)


st.set_page_config(page_title="Hybrid Retrieval Demo", layout="wide")
st.title("🧠 Hybrid Vector + Graph Retrieval")

page = st.sidebar.selectbox("Choose a Mode", ["Ingestion", "Search", "Graph Visualization", "Database Inspector"])


if page == "Ingestion":
    st.header("📝 Document Ingestion")
    
    with st.form("ingest_form"):
        title = st.text_input("Document Title")
        text = st.text_area("Document Content", height=200)
        submitted = st.form_submit_button("Ingest Document")
        
        if submitted and text:
            with st.spinner("Ingesting..."):
                success, result = api_request("POST", "/nodes", json={
                    "title": title,
                    "text": text,
                    "metadata": {"source": "streamlit"}
                })
                if success:
                    st.success(f"Document '{title}' ingested successfully!")
                    st.json(result)
                else:
                    st.error(f"Error: {result}")

    st.markdown("---")
    st.header("🔗 Create Relationship")
    
    with st.form("edge_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            source = st.text_input("Source Node ID")
        with col2:
            target = st.text_input("Target Node ID")
        with col3:
            rel_type = st.text_input("Relationship Type", value="RELATED_TO")
            
        if st.form_submit_button("Create Edge") and source and target:
            success, result = api_request("POST", "/edges", json={
                "source": source,
                "target": target,
                "type": rel_type,
                "weight": 1.0
            })
            if success:
                st.success("Edge created!")
                st.json(result)
            else:
                st.error(f"Error: {result}")


# =============================================================================
# SEARCH PAGE
# =============================================================================
elif page == "Search":
    st.header("🔍 Hybrid Search")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search Query")
    with col2:
        search_type = st.selectbox("Search Type", ["Hybrid", "Vector Only", "Graph Search"])
    
    # Weight controls for hybrid search
    alpha, beta = 0.7, 0.3
    if search_type == "Hybrid":
        col_a, col_b = st.columns(2)
        with col_a:
            alpha = st.slider("Vector Weight (α)", 0.0, 1.0, 0.7)
        with col_b:
            beta = 1.0 - alpha
            st.metric("Graph Weight (β)", f"{beta:.2f}")
    
    if st.button("Search") and query:
        
        # ----- GRAPH SEARCH -----
        if search_type == "Graph Search":
            with st.spinner("Resolving query and fetching graph..."):
                # Resolve query to document ID via vector search
                success, v_result = api_request("POST", "/search/vector", json={"query_text": query, "top_k": 1})
                
                if not success:
                    st.error(f"Vector Resolution Error: {v_result}")
                elif not v_result:
                    st.warning("No matching concepts found to start graph search.")
                else:
                    start_id = v_result[0]['id']
                    start_title = v_result[0].get('metadata', {}).get('title', 'Untitled')
                    st.info(f"Starting Graph Search from: {start_title} (ID: {start_id})")
                    
                    # Fetch graph
                    success, data = api_request("GET", "/search/graph", params={"start_id": start_id, "depth": 2})
                    
                    if not success:
                        st.error(f"Graph Search Error: {data}")
                    else:
                        raw_nodes = data.get("nodes", [])
                        raw_edges = data.get("edges", [])
                        
                        # Build and render graph
                        nodes, edges = build_graph_objects(raw_nodes, raw_edges, start_id, node_size=18)
                        render_graph(nodes, edges)
                        
                        st.markdown("---")
                        
                        # Display scored edges
                        scored_edges = data.get("scored_edges", [])
                        st.subheader("🔗 Matching Edges (Sorted by Relevance)")
                        
                        if scored_edges:
                            st.info(f"Found {len(scored_edges)} edges in the graph")
                            for idx, edge in enumerate(scored_edges[:20], 1):
                                source_label = edge.get('source_title', edge['source'][:20])
                                target_label = edge.get('target_title', edge['target'][:20])
                                
                                with st.expander(f"#{idx} | {edge['type']} | {source_label} → {target_label} | Score: {edge['score']:.3f}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown("**Source**")
                                        st.caption(f"ID: `{edge['source']}`")
                                        if edge.get('source_title'):
                                            st.write(f"📄 {edge['source_title']}")
                                        if edge.get('source_snippet'):
                                            st.text(edge['source_snippet'])
                                    with col2:
                                        st.markdown("**Target**")
                                        st.caption(f"ID: `{edge['target']}`")
                                        if edge.get('target_title'):
                                            st.write(f"📄 {edge['target_title']}")
                                        if edge.get('target_snippet'):
                                            st.text(edge['target_snippet'])
                                    st.markdown(f"**Relationship:** `{edge['type']}` | **Weight:** {edge['weight']:.3f}")
                        else:
                            st.warning("No edges found in the graph")
                        
                        st.markdown("---")
                        
                        # Display nodes by level
                        adjacency = build_adjacency(raw_edges)
                        levels = compute_bfs_levels(start_id, adjacency)
                        display_nodes_by_level(nodes, levels)
        
        # ----- VECTOR / HYBRID SEARCH -----
        else:
            endpoint = "/search/hybrid" if search_type == "Hybrid" else "/search/vector"
            payload = {"query_text": query, "top_k": 5}
            
            if search_type == "Hybrid":
                payload.update({
                    "vector_weight": alpha,
                    "graph_weight": beta,
                    "graph_expand_depth": 1
                })
            
            with st.spinner("Searching..."):
                success, result = api_request("POST", endpoint, json=payload)
                
                if not success:
                    st.error(f"Error: {result}")
                else:
                    # Parse results (different format for hybrid vs vector)
                    items = result.get("results", []) if search_type == "Hybrid" else (result if isinstance(result, list) else result.get("results", []))
                    
                    if not items:
                        st.warning("No results found.")
                    else:
                        for item in items:
                            score = item.get('final_score', item.get('score', 0))
                            title = (item.get('text', '') or '')[:60] or 'Untitled'
                            
                            with st.expander(f"🔹 {score:.4f} | {title}"):
                                st.markdown(f"**ID:** `{item['id']}`")
                                st.write(item.get('text', ''))
                                
                                if search_type == "Hybrid":
                                    st.markdown("#### 📊 Score Breakdown")
                                    c1, c2, c3 = st.columns(3)
                                    c1.metric("Vector Score", f"{item.get('vector_score', 0):.4f}")
                                    c2.metric("Graph Score", f"{item.get('graph_score', 0):.4f}")
                                    c3.metric("Final Score", f"{item.get('final_score', 0):.4f}")
                                    
                                    info = item.get('info', {})
                                    if info:
                                        c4, c5 = st.columns(2)
                                        c4.metric("Hops", info.get('hop', 0))
                                        c5.metric("Connectivity (raw)", f"{info.get('connectivity_score_raw', 0)}")
                                else:
                                    st.metric("Score", f"{score:.4f}")
                
# =============================================================================
# GRAPH VISUALIZATION PAGE
# =============================================================================
elif page == "Graph Visualization":
    st.header("🕸️ Graph Visualization")
    
    search_mode = st.radio("Search Mode", ["By Node ID", "By Text Query"], horizontal=True)
    
    # Resolve start_id
    start_id = None
    if search_mode == "By Node ID":
        start_id = st.text_input("Start Node ID (for neighborhood)")
    else:
        text_query = st.text_input("Search Concept (e.g. 'Neo4j')")
        if text_query:
            success, results = api_request("POST", "/search/vector", json={"query_text": text_query, "top_k": 1})
            if success and results:
                start_id = results[0]['id']
                title = results[0].get('metadata', {}).get('title', 'Untitled')
                st.info(f"Resolved '{text_query}' to Node ID: {start_id} ({title})")
            elif success:
                st.warning("No matching concepts found.")
            else:
                st.error(f"Resolution Error: {results}")
    
    # Visualization options
    max_nodes = st.slider("Max nodes to display", 10, 300, 80, 10)
    max_neighbors = st.slider("Max neighbors per node", 2, 30, 10, 1)
    
    show_documents = st.checkbox("Show Documents", value=True)
    show_entities = st.checkbox("Show Entities", value=True)
    show_attributes = st.checkbox("Show Attributes / Values", value=False)
    show_edge_labels_around_start = st.checkbox("Show edge labels only around start node", value=True)
    
    if st.button("Visualize") and start_id:
        with st.spinner("Fetching graph data..."):
            success, data = api_request("GET", "/search/graph", params={"start_id": start_id, "depth": 1})
            
            if not success:
                st.error(f"Error: {data}")
            else:
                raw_nodes = data.get("nodes", [])
                raw_edges = data.get("edges", [])
                
                # Build adjacency and select nodes via BFS with limits
                adjacency = {}
                for e in raw_edges:
                    s, t = e["source"], e["target"]
                    adjacency.setdefault(s, set()).add(t)
                    adjacency.setdefault(t, set()).add(s)
                
                selected_ids = {start_id}
                queue = [start_id]
                while queue and len(selected_ids) < max_nodes:
                    current = queue.pop(0)
                    for nb in list(adjacency.get(current, []))[:max_neighbors]:
                        if len(selected_ids) >= max_nodes:
                            break
                        if nb not in selected_ids:
                            selected_ids.add(nb)
                            queue.append(nb)
                
                # Filter nodes by type visibility
                def is_visible(node):
                    if node["id"] not in selected_ids:
                        return False
                    labels = node.get("labels", [])
                    ntype = node.get("type")
                    
                    is_doc = "Document" in labels or ntype == "Document"
                    is_ent = "Entity" in labels or ntype == "Entity"
                    is_attr = "Attribute" in labels or "Value" in labels or ntype in ("Attribute", "Value")
                    
                    if is_doc and not show_documents:
                        return False
                    if is_ent and not show_entities:
                        return False
                    if is_attr and not show_attributes:
                        return False
                    return True
                
                filtered_nodes = [n for n in raw_nodes if is_visible(n)]
                visible_ids = {n["id"] for n in filtered_nodes}
                filtered_edges = [e for e in raw_edges if e["source"] in visible_ids and e["target"] in visible_ids]
                
                # Build and render
                nodes, edges = build_graph_objects(
                    filtered_nodes, filtered_edges, start_id, 
                    node_size=15, 
                    show_all_edge_labels=not show_edge_labels_around_start
                )
                render_graph(nodes, edges, width=1100, collapsible=True)
                
                st.info(f"Nodes shown: {len(nodes)} (from {len(raw_nodes)} total), Edges shown: {len(edges)} (from {len(raw_edges)} total)")


# =============================================================================
# DATABASE INSPECTOR PAGE
# =============================================================================
elif page == "Database Inspector":
    st.header("🕵️ Database Inspector")
    
    tab1, tab2, tab3 = st.tabs(["Neo4j Documents", "Neo4j Entities", "FAISS Index"])
    
    with tab1:
        st.subheader("Stored Documents")
        if st.button("Refresh Documents"):
            success, docs = api_request("GET", "/debug/documents")
            if success:
                st.write(f"Total Documents: {len(docs)}")
                
                doc_list = [{
                    "ID": d.get("id"),
                    "Title": d.get("title"),
                    "Vector ID": d.get("vector_id"),
                    "Text": (d.get("text", "")[:50] + "...") if d.get("text") else ""
                } for d in docs]
                
                st.dataframe(doc_list, use_container_width=True)
                
                st.markdown("### Document Details")
                selected_id = st.selectbox("Select Document ID to inspect", [d["ID"] for d in doc_list])
                if selected_id:
                    selected_doc = next((d for d in docs if d["id"] == selected_id), None)
                    st.json(selected_doc)
                    
                    if selected_doc and selected_doc.get("vector_id") is not None:
                        vid = selected_doc["vector_id"]
                        st.markdown(f"**Vector Embedding (ID: {vid})**")
                        v_success, v_data = api_request("GET", f"/debug/faiss/vector/{vid}")
                        if v_success:
                            vec = v_data["embedding"]
                            st.write(f"Dimension: {len(vec)}")
                            st.line_chart(vec)
                        else:
                            st.warning("Could not fetch vector data.")
            else:
                st.error("Failed to fetch documents")
    
    with tab2:
        st.subheader("Stored Entities")
        if st.button("Refresh Entities"):
            success, ents = api_request("GET", "/debug/entities")
            if success:
                st.write(f"Total Entities: {len(ents)}")
                ent_list = [{"ID": e.get("id"), "Name": e.get("name"), "Type": e.get("type")} for e in ents]
                st.dataframe(ent_list, use_container_width=True)
            else:
                st.error("Failed to fetch entities")
    
    with tab3:
        st.subheader("Vector Index Stats")
        if st.button("Refresh Stats"):
            success, info = api_request("GET", "/debug/faiss/info")
            if success:
                st.json(info)
                st.markdown("### ID Mapping")
                st.write("Mapping from FAISS Vector ID to Neo4j Document ID:")
                st.dataframe(info.get("id_map", {}), use_container_width=True)
            else:
                st.error("Failed to fetch FAISS info")
