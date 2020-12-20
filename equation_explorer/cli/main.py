import typer
from typing import List
from rich.console import Console
from rich.table import Table
import networkx as nx
from equation_explorer.core.registry import Registry
from equation_explorer.graph.knowledge_graph import PhysicsGraph
from equation_explorer.solver.engine import SolverEngine

app = typer.Typer(name="eqx", help="Equation Explorer CLI")
console = Console()

registry = Registry()

@app.callback()
def main_callback():
    registry.load_from_directory("corpus")
    try:
        registry.validate()
    except ValueError as e:
        console.print(f"[bold red]Corpus validation error:[/bold red]\n{e}")
        raise typer.Exit(1)

@app.command()
def show(equation_id: str):
    """Show details of an equation."""
    eq = registry.equations.get(equation_id)
    if not eq:
        console.print(f"[red]Equation '{equation_id}' not found in corpus.[/red]")
        raise typer.Exit(1)
        
    console.print(f"[bold blue]{eq.name.get('en', equation_id)}[/bold blue]")
    if eq.description:
        console.print(f"{eq.description}")
        
    console.print(f"\n[bold]Expression:[/bold] {eq.expression}")
    
    table = Table(title="Variables")
    table.add_column("Symbol", style="cyan")
    table.add_column("Quantity/Constant", style="magenta")
    table.add_column("Type")
    
    for sym, binding in eq.variables.items():
        if binding.quantity in registry.quantities:
            table.add_row(sym, binding.quantity, "Quantity")
        elif binding.quantity in registry.constants:
            table.add_row(sym, binding.quantity, "Constant")
        else:
            table.add_row(sym, binding.quantity, "Unknown")
            
    console.print(table)
    
    if eq.assumptions:
        console.print("\n[bold]Assumptions:[/bold]")
        for a_id in eq.assumptions:
            ast = registry.assumptions.get(a_id)
            if ast:
                console.print(f" - {a_id}: {ast.description}")
            else:
                console.print(f" - {a_id}")

@app.command()
def possible(known: List[str] = typer.Option(..., "--known", "-k", help="List of known quantities")):
    """What can be calculated from known quantities?"""
    graph = PhysicsGraph(registry)
    results = graph.find_what_can_calculate(known)
    if not results:
        console.print("[yellow]No direct calculations possible with those knowns.[/yellow]")
        return
        
    console.print("[bold green]You can calculate the following quantities (1-step):[/bold green]")
    for r in results:
        q = registry.quantities.get(r)
        name = q.name.get("en", r) if q else r
        console.print(f" - [cyan]{r}[/cyan] ({name})")

@app.command()
def path(source: str, target: str):
    """Find derivation path from source equation to target equation."""
    graph = PhysicsGraph(registry)
    p = graph.path_between_equations(source, target)
    if not p:
        console.print(f"[red]No derivation path found from {source} to {target}[/red]")
        return
        
    console.print(f"[bold green]Path from {source} to {target}:[/bold green]")
    for i, eq_id in enumerate(p):
        eq = registry.equations.get(eq_id)
        name = eq.name.get("en", eq_id) if eq else eq_id
        console.print(f" {i+1}. [cyan]{eq_id}[/cyan] ({name})")

@app.command()
def solve(eq_id: str, target: str):
    """Symbolically solve an equation for a target variable."""
    solver = SolverEngine(registry)
    try:
        solutions = solver.solve_equation(eq_id, target)
        console.print(f"[bold green]Solutions for {target} in {eq_id}:[/bold green]")
        for s in solutions:
            console.print(f" {target} = {s}")
    except Exception as e:
        console.print(f"[bold red]Failed to solve:[/bold red] {e}")

@app.command()
def what_breaks(eq_id: str):
    """Show assumptions that would break if removed."""
    eq = registry.equations.get(eq_id)
    if not eq:
        console.print(f"[red]Equation {eq_id} not found[/red]")
        return
    if not eq.assumptions:
        console.print("[green]No specific assumptions declared.[/green]")
        return
    console.print(f"[bold yellow]Assumptions required for {eq_id}:[/bold yellow]")
    for a in eq.assumptions:
        ast = registry.assumptions.get(a)
        desc = ast.description if ast else "Unknown assumption"
        console.print(f" - [bold]{a}[/bold]: {desc}")

@app.command()
def missing(eq_id: str, known: List[str] = typer.Option(..., "--known", "-k", help="List of known quantities")):
    """What variables are missing to solve this equation?"""
    eq = registry.equations.get(eq_id)
    if not eq:
        console.print(f"[red]Equation {eq_id} not found[/red]")
        return
        
    missing_vars = []
    for sym, binding in eq.variables.items():
        if binding.quantity not in known and binding.quantity not in registry.constants:
            missing_vars.append(binding.quantity)
            
    if not missing_vars:
        console.print("[bold green]Nothing. You have all required variables.[/bold green]")
    else:
        console.print(f"[bold red]You are missing:[/bold red] {missing_vars}")

@app.command()
def generalize(eq_id: str, remove: str = typer.Option(..., "--remove", help="Assumption to remove")):
    """Find a more general equation by removing an assumption."""
    # Find equations that derive to eq_id
    eq = registry.equations.get(eq_id)
    if not eq:
        console.print(f"[red]Equation {eq_id} not found[/red]")
        return
        
    if remove not in eq.assumptions:
        console.print(f"[yellow]{remove} is not an assumption of {eq_id}.[/yellow]")
        return
        
    console.print(f"[cyan]Searching for generalization of {eq_id} without {remove}...[/cyan]")
    for p_id in eq.derives_from:
        parent = registry.equations.get(p_id)
        if parent and remove not in parent.assumptions:
            console.print(f" -> Found more general form: [bold green]{p_id}[/bold green] ({parent.expression})")

@app.command()
def lint():
    """Lint the corpus for schema and dimensional errors."""
    console.print("[cyan]Linting corpus...[/cyan]")
    errors = 0
    solver = SolverEngine(registry)
    for eq_id, eq in registry.equations.items():
        if not solver.validate_dimensions(eq_id):
            console.print(f"[red]Dimensional error in {eq_id}[/red]")
            errors += 1
            
    # Check for orphan equations
    graph = PhysicsGraph(registry)
    orphans = list(nx.isolates(graph.G))
    for orphan in orphans:
        if orphan.startswith("equation:"):
            console.print(f"[yellow]Warning: Orphan equation {orphan}[/yellow]")
            
    if errors == 0:
        console.print("[bold green]Lint passed![/bold green]")
    else:
        console.print(f"[bold red]Lint failed with {errors} errors.[/bold red]")

@app.command()
def scaffold_corpus():
    """Generates basic corpus YAMLs to get started."""
    pass

if __name__ == "__main__":
    app()
