import networkx as nx
from typing import List, Set, Dict, Optional, Tuple
from equation_explorer.core.registry import Registry

class PhysicsGraph:
    def __init__(self, registry: Registry):
        self.registry = registry
        self.G = nx.DiGraph()
        self._build_graph()
        
    def _build_graph(self):
        # Nodes: Equations, Quantities
        for q_id, q in self.registry.quantities.items():
            self.G.add_node(f"quantity:{q_id}", type="quantity", data=q)
        for c_id, c in self.registry.constants.items():
            self.G.add_node(f"constant:{c_id}", type="constant", data=c)
        for a_id, a in self.registry.assumptions.items():
            self.G.add_node(f"assumption:{a_id}", type="assumption", data=a)

        for eq_id, eq in self.registry.equations.items():
            eq_node = f"equation:{eq_id}"
            self.G.add_node(eq_node, type="equation", data=eq)
            
            for local_sym, binding in eq.variables.items():
                if binding.quantity in self.registry.quantities:
                    q_node = f"quantity:{binding.quantity}"
                    self.G.add_edge(eq_node, q_node, relation="has_variable", symbol=local_sym)
                    self.G.add_edge(q_node, eq_node, relation="used_in", symbol=local_sym)
                elif binding.quantity in self.registry.constants:
                    c_node = f"constant:{binding.quantity}"
                    self.G.add_edge(eq_node, c_node, relation="has_constant", symbol=local_sym)
                    self.G.add_edge(c_node, eq_node, relation="used_in", symbol=local_sym)
                    
            for p_id in eq.derives_from:
                if p_id in self.registry.equations:
                    self.G.add_edge(f"equation:{p_id}", eq_node, relation="derives_to")
                    self.G.add_edge(eq_node, f"equation:{p_id}", relation="derives_from")
                    
            for a_id in eq.assumptions:
                if a_id in self.registry.assumptions:
                    self.G.add_edge(f"assumption:{a_id}", eq_node, relation="assumed_by")
                    self.G.add_edge(eq_node, f"assumption:{a_id}", relation="assumes")

    def find_equations_for_target(self, known_quantities: List[str], target_quantity: str) -> List[str]:
        """
        Find equations that can solve for target_quantity directly using known_quantities.
        """
        target_node = f"quantity:{target_quantity}"
        if target_node not in self.G:
            return []
            
        candidate_equations = []
        for eq_node in self.G.successors(target_node):
            if self.G.edges[target_node, eq_node].get("relation") == "used_in":
                eq_data = self.G.nodes[eq_node]["data"]
                
                # Check if all other variables in the equation are known or constants
                can_solve = True
                for sym, binding in eq_data.variables.items():
                    if binding.quantity != target_quantity:
                        if binding.quantity not in known_quantities and binding.quantity not in self.registry.constants:
                            can_solve = False
                            break
                if can_solve:
                    candidate_equations.append(eq_data.id)
                    
        return candidate_equations
        
    def find_what_can_calculate(self, known_quantities: List[str]) -> List[str]:
        """
        Returns a list of quantity IDs that can be calculated given the known_quantities (1 step).
        """
        calculable = set()
        
        for eq_id, eq in self.registry.equations.items():
            unknowns = []
            for sym, binding in eq.variables.items():
                if binding.quantity not in known_quantities and binding.quantity not in self.registry.constants:
                    unknowns.append(binding.quantity)
            
            if len(unknowns) == 1:
                calculable.add(unknowns[0])
                
        return list(calculable)
        
    def path_between_equations(self, source_eq: str, target_eq: str) -> List[str]:
        source_node = f"equation:{source_eq}"
        target_node = f"equation:{target_eq}"
        
        # We only traverse 'derives_to' relations to find a derivation path
        # Create a subgraph with only derives_to
        view = nx.subgraph_view(self.G, filter_edge=lambda u, v: self.G[u][v].get("relation") == "derives_to")
        try:
            path = nx.shortest_path(view, source=source_node, target=target_node)
            return [node.replace("equation:", "") for node in path]
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            return []
