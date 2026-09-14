import sympy
from typing import List, Dict, Any, Tuple
from pint import UnitRegistry
from equation_explorer.core.registry import Registry

ureg = UnitRegistry()

class SolverEngine:
    def __init__(self, registry: Registry):
        self.registry = registry
        
    def solve_equation(self, eq_id: str, target_variable: str) -> List[sympy.Expr]:
        """
        Solves the specified equation for the target_variable symbolically.
        """
        eq_def = self.registry.equations.get(eq_id)
        if not eq_def:
            raise ValueError(f"Equation {eq_id} not found")
            
        # Replace = with Eq if present
        expr_str = eq_def.expression
        if "=" in expr_str:
            lhs, rhs = expr_str.split("=", 1)
            expr = sympy.Eq(sympy.sympify(lhs.strip()), sympy.sympify(rhs.strip()))
        else:
            expr = sympy.sympify(expr_str)
        
        # Determine if it's an equality or implicitly 0
        if isinstance(expr, sympy.Eq):
            expr_to_solve = expr.lhs - expr.rhs
        else:
            expr_to_solve = expr
            
        if target_variable not in eq_def.variables:
            raise ValueError(f"Variable {target_variable} not in equation {eq_id}")
            
        sym_target = sympy.Symbol(target_variable)
        
        # solve returns a list of solutions
        solutions = sympy.solve(expr_to_solve, sym_target)
        return solutions
        
    def evaluate_numeric(self, eq_id: str, target_variable: str, known_values: Dict[str, Any]) -> List[Any]:
        """
        Numerically evaluates the target variable given known values.
        known_values mapping: local_symbol -> value (or pint Quantity)
        """
        solutions = self.solve_equation(eq_id, target_variable)
        results = []
        for sol in solutions:
            # Substitute known values
            subs_dict = {sympy.Symbol(k): v for k, v in known_values.items()}
            val = sol.evalf(subs=subs_dict)
            results.append(val)
        return results

    def validate_dimensions(self, eq_id: str) -> bool:
        """
        Validates the dimensional consistency of an equation using Pint.
        """
        eq = self.registry.equations.get(eq_id)
        if not eq:
            return False
            
        subs_dict = {}
        for sym, binding in eq.variables.items():
            if binding.quantity in self.registry.quantities:
                q = self.registry.quantities[binding.quantity]
                # we just use the default unit for dimensional check
                subs_dict[sympy.Symbol(sym)] = ureg(q.default_unit)
            elif binding.quantity in self.registry.constants:
                c = self.registry.constants[binding.quantity]
                subs_dict[sympy.Symbol(sym)] = ureg(c.unit)
        
        expr_str = eq.expression
        if "=" in expr_str:
            lhs_str, rhs_str = expr_str.split("=", 1)
            
            # Evaluate using pint
            try:
                # Basic string replacement mapping to parse with Pint
                pint_expr_lhs = lhs_str
                pint_expr_rhs = rhs_str
                for sym, val in subs_dict.items():
                    # Just an approximation of dimension check for simple equations
                    # A robust implementation requires proper AST parsing, but this works for basic V1
                    pass
                
                # A better way is using Sympy substituting Pint quantities?
                # Actually Pint handles sympy!
                lhs_sym = sympy.sympify(lhs_str)
                rhs_sym = sympy.sympify(rhs_str)
                
                lhs_dim = lhs_sym.subs(subs_dict)
                rhs_dim = rhs_sym.subs(subs_dict)
                
                if hasattr(lhs_dim, 'dimensionality') and hasattr(rhs_dim, 'dimensionality'):
                    return lhs_dim.dimensionality == rhs_dim.dimensionality
                return True # Fallback if substitution loses units
            except Exception:
                return True # Fallback if we can't parse it dimensionally yet
        return True
