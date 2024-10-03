from dataclasses import dataclass, field
from typing import List, Optional, Dict, Callable, Any

from src.utils.time_utils import convert_timestamps


@dataclass
class SubgraphClientConfig:
    method_name: str
    pagination_field: str
    ignore_columns: List[str] = field(default_factory=lambda: ["tenant"])
    tenant_needed_fields: Optional[List[str]] = field(default_factory=list)
    name_maps: Optional[Dict[str, str]] = field(default_factory=dict)  # model_name -> subgraph_name
    converter: Optional[Callable[[Any], Any]] = convert_timestamps
