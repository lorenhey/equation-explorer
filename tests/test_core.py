import pytest
import os
from equation_explorer.core.registry import Registry
from equation_explorer.solver.engine import SolverEngine
from equation_explorer.graph.knowledge_graph import PhysicsGraph

@pytest.fixture
def registry():
    r = Registry()
    r.load_from_directory("corpus")
    r.validate()
    return r

def test_registry_loading(registry):
    assert "newton.second_law" in registry.equations
    assert "mass" in registry.quantities

def test_solve_engine(registry):
    solver = SolverEngine(registry)
    # F = m * a  => a = F / m
    sols = solver.solve_equation("newton.second_law", "a")
    assert len(sols) == 1
    assert str(sols[0]) == "F/m"
    
def test_dimensional_validation(registry):
    solver = SolverEngine(registry)
    # Assuming newton.second_law is valid
    assert solver.validate_dimensions("newton.second_law") is True

def test_graph_path(registry):
    graph = PhysicsGraph(registry)
    path = graph.path_between_equations("newton.second_law", "orbital.centripetal_force")
    assert path == ["newton.second_law", "orbital.centripetal_force"]
    
def test_what_can_calculate(registry):
    graph = PhysicsGraph(registry)
    calc = graph.find_what_can_calculate(["mass", "acceleration"])
    assert "force" in calc
