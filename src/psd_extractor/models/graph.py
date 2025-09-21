"""
Expression graph data models.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class GraphParams:
    """Graph runtime parameters."""

    valence: float = 0.0
    arousal: float = 0.0
    speaking: bool = False
    emotion: str = "neutral"
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "valence": self.valence,
            "arousal": self.arousal,
            "speaking": self.speaking,
            "emotion": self.emotion,
        }
        result.update(self.custom)
        return result


@dataclass
class SlotState:
    """State definition for a single slot."""

    viseme: Optional[str] = None
    emotion: Optional[str] = None
    state: Optional[str] = None
    shape: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        if self.viseme is not None:
            result["viseme"] = self.viseme
        if self.emotion is not None:
            result["emotion"] = self.emotion
        if self.state is not None:
            result["state"] = self.state
        if self.shape is not None:
            result["shape"] = self.shape
        return result


@dataclass
class GraphNode:
    """A node in the expression graph representing a facial state."""

    slots: Dict[str, SlotState] = field(default_factory=dict)
    duration: Optional[List[int]] = None  # [min_ms, max_ms] for random duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "slots": {
                slot_name: slot_state.to_dict()
                for slot_name, slot_state in self.slots.items()
            }
        }
        if self.duration:
            result["duration"] = self.duration
        return result


@dataclass
class GraphEdge:
    """An edge in the expression graph defining state transitions."""

    from_node: str
    to_node: str
    condition: str
    on_enter: bool = False
    after: Optional[Union[int, List[int]]] = None  # ms or [min_ms, max_ms]
    prob: Optional[float] = None  # probability 0.0-1.0
    on_event: Optional[str] = None
    while_condition: Optional[str] = None
    cooldown: Optional[int] = None  # ms

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"from": self.from_node, "to": self.to_node}

        if self.on_enter:
            result["onEnter"] = True
        if self.after is not None:
            result["after"] = self.after
        if self.prob is not None:
            result["prob"] = self.prob
        if self.on_event is not None:
            result["onEvent"] = self.on_event
        if self.while_condition is not None:
            result["while"] = self.while_condition
        if self.cooldown is not None:
            result["cooldown"] = self.cooldown

        return result


@dataclass
class ExpressionGraph:
    """Complete expression graph defining state machine behavior."""

    schema: str = "./schemas/graph.schema.json"
    params: GraphParams = field(default_factory=GraphParams)
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "$schema": self.schema,
            "params": self.params.to_dict(),
            "nodes": {
                node_name: node.to_dict() for node_name, node in self.nodes.items()
            },
            "edges": [edge.to_dict() for edge in self.edges],
        }
