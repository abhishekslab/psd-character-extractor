"""
Expression Graph Builder

Builds expression state machines for avatar animation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models.avatar import AvatarBundle
from .models.graph import ExpressionGraph, GraphEdge, GraphNode, GraphParams, SlotState

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds expression graphs (state machines) for avatar animation."""

    def __init__(self, avatar_bundle: AvatarBundle):
        """
        Initialize the graph builder.

        Args:
            avatar_bundle: Avatar bundle to build graph for
        """
        self.avatar = avatar_bundle

    def build_idle_talk_graph(self) -> ExpressionGraph:
        """
        Build a basic idle-talk expression graph.

        Returns:
            ExpressionGraph with idle, blink, and talk states
        """
        graph = ExpressionGraph()

        # Set initial parameters
        graph.params = GraphParams(
            valence=0.1, arousal=0.2, speaking=False, emotion="neutral"
        )

        # Build nodes
        graph.nodes = self._build_idle_talk_nodes()

        # Build edges
        graph.edges = self._build_idle_talk_edges()

        logger.info("Built idle-talk expression graph")
        return graph

    def build_full_emotion_graph(self) -> ExpressionGraph:
        """
        Build a comprehensive emotion-aware expression graph.

        Returns:
            ExpressionGraph with emotional states and reactions
        """
        graph = ExpressionGraph()

        # Set initial parameters
        graph.params = GraphParams(
            valence=0.0, arousal=0.0, speaking=False, emotion="neutral"
        )

        # Build nodes with emotional variations
        graph.nodes = self._build_emotion_nodes()

        # Build edges with emotion triggers
        graph.edges = self._build_emotion_edges()

        logger.info("Built full emotion expression graph")
        return graph

    def _build_idle_talk_nodes(self) -> Dict[str, GraphNode]:
        """Build basic idle-talk nodes."""
        nodes = {}

        # Idle neutral state
        idle_slots = {}
        if "Mouth" in self.avatar.slots:
            idle_slots["Mouth"] = SlotState(viseme="REST")
        if "EyeL" in self.avatar.slots:
            idle_slots["EyeL"] = SlotState(state="open")
        if "EyeR" in self.avatar.slots:
            idle_slots["EyeR"] = SlotState(state="open")

        nodes["IdleNeutral"] = GraphNode(slots=idle_slots)

        # Blink state
        blink_slots = idle_slots.copy()
        if "EyeL" in self.avatar.slots:
            blink_slots["EyeL"] = SlotState(state="closed")
        if "EyeR" in self.avatar.slots:
            blink_slots["EyeR"] = SlotState(state="closed")

        nodes["IdleBlink"] = GraphNode(
            slots=blink_slots, duration=[120, 180]  # Quick blink
        )

        # Talk state
        talk_slots = idle_slots.copy()
        if "Mouth" in self.avatar.slots:
            talk_slots["Mouth"] = SlotState(viseme="AUTO")  # Let lipsync drive this

        nodes["TalkNeutral"] = GraphNode(slots=talk_slots)

        return nodes

    def _build_idle_talk_edges(self) -> List[GraphEdge]:
        """Build basic idle-talk edges."""
        edges = []

        # Idle to blink (random)
        edges.append(
            GraphEdge(
                from_node="IdleNeutral",
                to_node="IdleBlink",
                condition="random",
                after=[2000, 6000],  # 2-6 seconds
                prob=0.6,
            )
        )

        # Blink back to idle (immediate)
        edges.append(
            GraphEdge(
                from_node="IdleBlink",
                to_node="IdleNeutral",
                condition="onEnter",
                on_enter=True,
            )
        )

        # Idle to talk (when speaking)
        edges.append(
            GraphEdge(
                from_node="IdleNeutral",
                to_node="TalkNeutral",
                condition="while",
                while_condition="speaking",
            )
        )

        # Talk back to idle (when not speaking)
        edges.append(
            GraphEdge(
                from_node="TalkNeutral",
                to_node="IdleNeutral",
                condition="while",
                while_condition="!speaking",
            )
        )

        return edges

    def _build_emotion_nodes(self) -> Dict[str, GraphNode]:
        """Build emotion-aware nodes."""
        nodes = self._build_idle_talk_nodes()  # Start with basic nodes

        # Add emotional variations
        base_slots = {}
        if "Mouth" in self.avatar.slots:
            base_slots["Mouth"] = SlotState(viseme="REST")
        if "EyeL" in self.avatar.slots:
            base_slots["EyeL"] = SlotState(state="open")
        if "EyeR" in self.avatar.slots:
            base_slots["EyeR"] = SlotState(state="open")

        # Happy/smile state
        smile_slots = base_slots.copy()
        if "Mouth" in self.avatar.slots:
            # Check if emotion is available
            mouth_slot = self.avatar.slots["Mouth"]
            if mouth_slot.emotions and "smile" in mouth_slot.emotions:
                smile_slots["Mouth"] = SlotState(emotion="smile")

        if "BrowL" in self.avatar.slots:
            brow_slot = self.avatar.slots["BrowL"]
            if brow_slot.shapes and "up" in brow_slot.shapes:
                smile_slots["BrowL"] = SlotState(shape="up")

        if "BrowR" in self.avatar.slots:
            brow_slot = self.avatar.slots["BrowR"]
            if brow_slot.shapes and "up" in brow_slot.shapes:
                smile_slots["BrowR"] = SlotState(shape="up")

        nodes["Smile"] = GraphNode(slots=smile_slots)

        # Sad state
        sad_slots = base_slots.copy()
        if "Mouth" in self.avatar.slots:
            mouth_slot = self.avatar.slots["Mouth"]
            if mouth_slot.emotions and "sad" in mouth_slot.emotions:
                sad_slots["Mouth"] = SlotState(emotion="sad")

        if "EyeL" in self.avatar.slots:
            eye_slot = self.avatar.slots["EyeL"]
            if eye_slot.states and "sad" in eye_slot.states:
                sad_slots["EyeL"] = SlotState(state="sad")

        if "EyeR" in self.avatar.slots:
            eye_slot = self.avatar.slots["EyeR"]
            if eye_slot.states and "sad" in eye_slot.states:
                sad_slots["EyeR"] = SlotState(state="sad")

        nodes["Sad"] = GraphNode(slots=sad_slots)

        # Surprised state
        surprised_slots = base_slots.copy()
        if "EyeL" in self.avatar.slots:
            surprised_slots["EyeL"] = SlotState(state="open")  # Wide open
        if "EyeR" in self.avatar.slots:
            surprised_slots["EyeR"] = SlotState(state="open")

        if "BrowL" in self.avatar.slots:
            brow_slot = self.avatar.slots["BrowL"]
            if brow_slot.shapes and "up" in brow_slot.shapes:
                surprised_slots["BrowL"] = SlotState(shape="up")

        if "BrowR" in self.avatar.slots:
            brow_slot = self.avatar.slots["BrowR"]
            if brow_slot.shapes and "up" in brow_slot.shapes:
                surprised_slots["BrowR"] = SlotState(shape="up")

        nodes["Surprised"] = GraphNode(slots=surprised_slots)

        return nodes

    def _build_emotion_edges(self) -> List[GraphEdge]:
        """Build emotion-aware edges."""
        edges = self._build_idle_talk_edges()  # Start with basic edges

        # Add emotion transitions
        # Idle to smile (on positive valence or joke event)
        edges.append(
            GraphEdge(
                from_node="IdleNeutral",
                to_node="Smile",
                condition="event",
                on_event="joke",
                cooldown=3000,  # 3 second cooldown
            )
        )

        # Smile back to idle (timer)
        edges.append(
            GraphEdge(
                from_node="Smile",
                to_node="IdleNeutral",
                condition="timer",
                after=[2000, 4000],  # 2-4 seconds
            )
        )

        # Idle to sad (on negative valence)
        edges.append(
            GraphEdge(
                from_node="IdleNeutral",
                to_node="Sad",
                condition="event",
                on_event="sad",
                cooldown=5000,  # 5 second cooldown
            )
        )

        # Sad back to idle (timer)
        edges.append(
            GraphEdge(
                from_node="Sad",
                to_node="IdleNeutral",
                condition="timer",
                after=[3000, 5000],  # 3-5 seconds
            )
        )

        # Idle to surprised (on surprise event)
        edges.append(
            GraphEdge(
                from_node="IdleNeutral",
                to_node="Surprised",
                condition="event",
                on_event="surprise",
                cooldown=2000,  # 2 second cooldown
            )
        )

        # Surprised back to idle (quick timer)
        edges.append(
            GraphEdge(
                from_node="Surprised",
                to_node="IdleNeutral",
                condition="timer",
                after=[800, 1200],  # 0.8-1.2 seconds
            )
        )

        return edges

    def save_graph(
        self, graph: ExpressionGraph, output_dir: str, filename: str = "graph.json"
    ) -> str:
        """
        Save expression graph to JSON file.

        Args:
            graph: Expression graph to save
            output_dir: Output directory
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = Path(output_dir) / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved expression graph: {output_path}")
        return str(output_path)

    @classmethod
    def create_preset_graphs(
        cls, avatar_bundle: AvatarBundle, output_dir: str
    ) -> Dict[str, str]:
        """
        Create preset graph templates.

        Args:
            avatar_bundle: Avatar bundle to create graphs for
            output_dir: Output directory

        Returns:
            Dictionary mapping preset names to file paths
        """
        builder = cls(avatar_bundle)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        preset_files = {}

        # Create idle-talk graph
        idle_talk_graph = builder.build_idle_talk_graph()
        preset_files["idle-talk"] = builder.save_graph(
            idle_talk_graph, output_dir, "graph.idle-talk.json"
        )

        # Create full emotion graph
        emotion_graph = builder.build_full_emotion_graph()
        preset_files["full-emotion"] = builder.save_graph(
            emotion_graph, output_dir, "graph.full-emotion.json"
        )

        logger.info(f"Created {len(preset_files)} preset graphs")
        return preset_files
