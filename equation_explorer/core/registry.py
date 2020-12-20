import os
import yaml
from typing import Dict, List
from equation_explorer.core.schema import Equation, Quantity, Constant, Assumption

class Registry:
    def __init__(self):
        self.equations: Dict[str, Equation] = {}
        self.quantities: Dict[str, Quantity] = {}
        self.constants: Dict[str, Constant] = {}
        self.assumptions: Dict[str, Assumption] = {}
    
    def load_from_directory(self, path: str):
        if not os.path.exists(path):
            return
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    self._load_file(os.path.join(root, file))
                    
    def _load_file(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not data:
            return
            
        if 'quantities' in data:
            for item in data['quantities']:
                q = Quantity(**item)
                self.quantities[q.id] = q
        
        if 'constants' in data:
            for item in data['constants']:
                c = Constant(**item)
                self.constants[c.id] = c
                
        if 'assumptions' in data:
            for item in data['assumptions']:
                a = Assumption(**item)
                self.assumptions[a.id] = a
                
        if 'equations' in data:
            for item in data['equations']:
                eq = Equation(**item)
                self.equations[eq.id] = eq

    def validate(self):
        errors = []
        for eq_id, eq in self.equations.items():
            for sym, binding in eq.variables.items():
                if binding.quantity not in self.quantities and binding.quantity not in self.constants:
                    errors.append(f"Equation {eq_id} references unknown quantity/constant: {binding.quantity}")
            for ast in eq.assumptions:
                if ast not in self.assumptions:
                    errors.append(f"Equation {eq_id} references unknown assumption: {ast}")
            for p_id in eq.derives_from:
                if p_id not in self.equations:
                    errors.append(f"Equation {eq_id} derives from unknown equation: {p_id}")
        if errors:
            raise ValueError("\n".join(errors))
