import streamlit as st
import os
import networkx as nx
from equation_explorer.core.registry import Registry
from equation_explorer.graph.knowledge_graph import PhysicsGraph
from equation_explorer.solver.engine import SolverEngine

st.set_page_config(page_title="Equation Explorer", layout="wide")

@st.cache_resource
def load_registry():
    r = Registry()
    if os.path.exists("corpus"):
        r.load_from_directory("corpus")
        try:
            r.validate()
        except ValueError as e:
            st.error(f"Corpus Validation Error: {e}")
    return r

registry = load_registry()
graph = PhysicsGraph(registry)
solver = SolverEngine(registry)

st.title("Equation Explorer")

tab1, tab2, tab3 = st.tabs(["Browse", "Solve", "Path Finder"])

with tab1:
    st.header("Corpus Explorer")
    eq_id = st.selectbox("Select Equation", options=list(registry.equations.keys()))
    if eq_id:
        eq = registry.equations[eq_id]
        st.subheader(eq.name.get("en", eq_id))
        st.latex(eq.expression)
        if eq.description:
            st.markdown(eq.description)
            
        st.markdown("### Variables")
        for sym, b in eq.variables.items():
            st.markdown(f"- **{sym}**: {b.quantity}")
            
        if eq.assumptions:
            st.markdown("### Assumptions")
            for a in eq.assumptions:
                st.markdown(f"- {a}")

with tab2:
    st.header("Symbolic Solver")
    solve_eq = st.selectbox("Equation to solve", options=list(registry.equations.keys()), key="solve_eq")
    if solve_eq:
        eq = registry.equations[solve_eq]
        st.latex(eq.expression)
        
        target = st.selectbox("Target Variable", options=list(eq.variables.keys()))
        if st.button("Solve"):
            try:
                sols = solver.solve_equation(solve_eq, target)
                for s in sols:
                    st.latex(f"{target} = {s}")
            except Exception as e:
                st.error(str(e))

with tab3:
    st.header("Derivation Path Finder")
    source = st.selectbox("Source Equation", options=list(registry.equations.keys()), key="path_source")
    target = st.selectbox("Target Equation", options=list(registry.equations.keys()), key="path_target")
    
    if st.button("Find Path"):
        p = graph.path_between_equations(source, target)
        if p:
            for i, node in enumerate(p):
                st.markdown(f"**{i+1}.** {node}")
        else:
            st.warning("No path found.")
