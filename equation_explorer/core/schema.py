from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class Quantity(BaseModel):
    id: str
    name: Dict[str, str]
    default_symbol: str
    dimension: str
    default_unit: str
    description: Optional[str] = None
    is_vector: bool = False

class Constant(BaseModel):
    id: str
    name: Dict[str, str]
    symbol: str
    value: float
    unit: str
    uncertainty: Optional[float] = None
    source: Optional[str] = None

class Assumption(BaseModel):
    id: str
    name: Dict[str, str]
    description: str

class VariableBinding(BaseModel):
    quantity: str
    description: Optional[str] = None

class DerivationStep(BaseModel):
    operation: str
    result: str
    justification: Optional[str] = None

class Derivation(BaseModel):
    steps: List[DerivationStep]
    source_equations: List[str] = Field(default_factory=list)

class Equation(BaseModel):
    id: str
    name: Dict[str, str]
    expression: str
    variables: Dict[str, VariableBinding]
    assumptions: List[str] = Field(default_factory=list)
    derives_from: List[str] = Field(default_factory=list)
    domain: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    derivation: Optional[Derivation] = None
