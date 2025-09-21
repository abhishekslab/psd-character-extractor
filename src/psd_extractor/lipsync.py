"""
Lipsync Pipeline

Handles phoneme-to-viseme mapping and animation scheduling for speaking avatars.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class VisemeType(Enum):
    """Standard viseme types for lip sync animation."""

    SIL = "SIL"  # Silence
    AI = "AI"  # Vowels: A, I
    E = "E"  # Vowel: E
    U = "U"  # Vowel: U
    O = "O"  # Vowel: O
    FV = "FV"  # Consonants: F, V
    L = "L"  # Consonant: L
    WQ = "WQ"  # Consonants: W, R, Q
    MBP = "MBP"  # Consonants: M, B, P
    REST = "REST"  # Rest/neutral position


@dataclass
class VisemeFrame:
    """A single viseme frame with timing information."""

    viseme: VisemeType
    start_time: float  # seconds
    duration: float  # seconds
    confidence: float = 1.0  # 0.0-1.0


@dataclass
class LipsyncData:
    """Complete lipsync data for an audio sequence."""

    frames: List[VisemeFrame]
    duration: float  # total duration in seconds
    sample_rate: int = 60  # fps for animation


class PhonemeMapper:
    """Maps phonemes to visemes using configurable rules."""

    # Default phoneme-to-viseme mapping based on standard speech recognition
    DEFAULT_PHONEME_MAPPING = {
        # Silence
        "SIL": VisemeType.SIL,
        "sil": VisemeType.SIL,
        # Vowels - AI group
        "AA": VisemeType.AI,  # father
        "AE": VisemeType.AI,  # cat
        "AH": VisemeType.AI,  # but
        "AY": VisemeType.AI,  # bite
        "IY": VisemeType.AI,  # beat
        "IH": VisemeType.AI,  # bit
        # Vowels - E group
        "EH": VisemeType.E,  # bet
        "EY": VisemeType.E,  # bait
        # Vowels - U group
        "UW": VisemeType.U,  # boot
        "UH": VisemeType.U,  # book
        # Vowels - O group
        "AO": VisemeType.O,  # bought
        "OW": VisemeType.O,  # boat
        "OY": VisemeType.O,  # boy
        # Consonants - F/V
        "F": VisemeType.FV,
        "V": VisemeType.FV,
        # Consonants - L
        "L": VisemeType.L,
        "EL": VisemeType.L,
        # Consonants - W/R
        "W": VisemeType.WQ,
        "R": VisemeType.WQ,
        "ER": VisemeType.WQ,
        # Consonants - M/B/P
        "M": VisemeType.MBP,
        "B": VisemeType.MBP,
        "P": VisemeType.MBP,
        "EM": VisemeType.MBP,
        # Other consonants default to REST
        "T": VisemeType.REST,
        "D": VisemeType.REST,
        "K": VisemeType.REST,
        "G": VisemeType.REST,
        "S": VisemeType.REST,
        "Z": VisemeType.REST,
        "SH": VisemeType.REST,
        "ZH": VisemeType.REST,
        "TH": VisemeType.REST,
        "DH": VisemeType.REST,
        "N": VisemeType.REST,
        "NG": VisemeType.REST,
        "CH": VisemeType.REST,
        "JH": VisemeType.REST,
        "HH": VisemeType.REST,
        "Y": VisemeType.REST,
    }

    def __init__(self, custom_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize phoneme mapper.

        Args:
            custom_mapping: Optional custom phoneme-to-viseme mapping
        """
        self.mapping = self.DEFAULT_PHONEME_MAPPING.copy()

        if custom_mapping:
            # Convert string viseme names to VisemeType enums
            for phoneme, viseme_str in custom_mapping.items():
                try:
                    viseme = VisemeType(viseme_str.upper())
                    self.mapping[phoneme.upper()] = viseme
                except ValueError:
                    logger.warning(f"Unknown viseme type: {viseme_str}")

    def map_phoneme(self, phoneme: str) -> VisemeType:
        """
        Map a single phoneme to a viseme.

        Args:
            phoneme: Phoneme string (e.g., 'AA', 'B', 'SIL')

        Returns:
            VisemeType corresponding to the phoneme
        """
        phoneme_upper = phoneme.upper()
        return self.mapping.get(phoneme_upper, VisemeType.REST)

    def map_phoneme_sequence(
        self, phonemes: List[Tuple[str, float, float]]
    ) -> List[VisemeFrame]:
        """
        Map a sequence of phonemes with timing to viseme frames.

        Args:
            phonemes: List of (phoneme, start_time, duration) tuples

        Returns:
            List of VisemeFrame objects
        """
        frames = []

        for phoneme, start_time, duration in phonemes:
            viseme = self.map_phoneme(phoneme)
            frame = VisemeFrame(viseme=viseme, start_time=start_time, duration=duration)
            frames.append(frame)

        return frames


class LipsyncPipeline:
    """Main lipsync pipeline for processing text/audio to viseme animations."""

    def __init__(self, phoneme_mapper: Optional[PhonemeMapper] = None):
        """
        Initialize lipsync pipeline.

        Args:
            phoneme_mapper: Optional custom phoneme mapper
        """
        self.phoneme_mapper = phoneme_mapper or PhonemeMapper()

    def process_text(self, text: str, speech_rate: float = 150.0) -> LipsyncData:
        """
        Process text to generate viseme sequence (simplified text-based approach).

        Args:
            text: Input text to process
            speech_rate: Words per minute for timing estimation

        Returns:
            LipsyncData with estimated viseme timing
        """
        # Simple text-to-viseme mapping (for demo purposes)
        # In production, this would use TTS + phoneme recognition

        words = text.lower().split()
        frames = []
        current_time = 0.0

        # Estimate timing based on speech rate
        chars_per_second = (speech_rate * 5) / 60.0  # Rough estimate

        for word in words:
            word_duration = len(word) / chars_per_second

            # Simple character-to-viseme mapping
            visemes = self._text_to_visemes(word)

            if visemes:
                viseme_duration = word_duration / len(visemes)

                for viseme in visemes:
                    frame = VisemeFrame(
                        viseme=viseme, start_time=current_time, duration=viseme_duration
                    )
                    frames.append(frame)
                    current_time += viseme_duration

            # Add small pause between words
            pause_frame = VisemeFrame(
                viseme=VisemeType.REST, start_time=current_time, duration=0.1
            )
            frames.append(pause_frame)
            current_time += 0.1

        total_duration = current_time

        return LipsyncData(frames=frames, duration=total_duration, sample_rate=60)

    def process_rhubarb_json(self, rhubarb_data: Dict[str, Any]) -> LipsyncData:
        """
        Process Rhubarb lipsync JSON output to generate viseme sequence.

        Args:
            rhubarb_data: JSON data from Rhubarb lipsync tool

        Returns:
            LipsyncData with precise timing from audio analysis
        """
        frames = []

        # Parse Rhubarb mouth cues
        mouth_cues = rhubarb_data.get("mouthCues", [])

        for cue in mouth_cues:
            start_time = cue.get("start", 0.0)
            value = cue.get("value", "X")  # Rhubarb uses A, B, C, D, E, F, G, H, X

            # Map Rhubarb mouth shapes to visemes
            viseme = self._rhubarb_to_viseme(value)

            # Calculate duration (use next cue's start time, or default)
            duration = 0.1  # Default frame duration

            frame = VisemeFrame(viseme=viseme, start_time=start_time, duration=duration)
            frames.append(frame)

        # Calculate actual durations
        for i, frame in enumerate(frames):
            if i < len(frames) - 1:
                frame.duration = frames[i + 1].start_time - frame.start_time
            else:
                # Last frame duration
                frame.duration = 0.1

        total_duration = frames[-1].start_time + frames[-1].duration if frames else 0.0

        return LipsyncData(frames=frames, duration=total_duration, sample_rate=60)

    def _text_to_visemes(self, word: str) -> List[VisemeType]:
        """
        Simple text-to-viseme mapping for basic text processing.

        Args:
            word: Word to convert

        Returns:
            List of visemes for the word
        """
        visemes = []
        word = word.lower()

        # Very basic vowel/consonant detection
        for char in word:
            if char in "aeiou":
                if char in "ai":
                    visemes.append(VisemeType.AI)
                elif char == "e":
                    visemes.append(VisemeType.E)
                elif char == "u":
                    visemes.append(VisemeType.U)
                elif char == "o":
                    visemes.append(VisemeType.O)
                else:
                    visemes.append(VisemeType.AI)
            elif char in "fv":
                visemes.append(VisemeType.FV)
            elif char == "l":
                visemes.append(VisemeType.L)
            elif char in "wr":
                visemes.append(VisemeType.WQ)
            elif char in "mbp":
                visemes.append(VisemeType.MBP)
            else:
                visemes.append(VisemeType.REST)

        return visemes

    def _rhubarb_to_viseme(self, rhubarb_shape: str) -> VisemeType:
        """
        Map Rhubarb mouth shapes to visemes.

        Args:
            rhubarb_shape: Rhubarb mouth shape (A-H, X)

        Returns:
            Corresponding VisemeType
        """
        # Rhubarb shape mapping
        rhubarb_mapping = {
            "A": VisemeType.REST,  # Closed mouth
            "B": VisemeType.MBP,  # M, B, P sounds
            "C": VisemeType.AI,  # Open vowels
            "D": VisemeType.AI,  # More open vowels
            "E": VisemeType.E,  # E vowel
            "F": VisemeType.FV,  # F, V sounds
            "G": VisemeType.U,  # U vowel
            "H": VisemeType.L,  # L sound
            "X": VisemeType.REST,  # Silence/rest
        }

        return rhubarb_mapping.get(rhubarb_shape.upper(), VisemeType.REST)

    def optimize_viseme_sequence(
        self, frames: List[VisemeFrame], min_duration: float = 0.05
    ) -> List[VisemeFrame]:
        """
        Optimize viseme sequence by merging short frames and smoothing transitions.

        Args:
            frames: Input viseme frames
            min_duration: Minimum frame duration in seconds

        Returns:
            Optimized viseme frames
        """
        if not frames:
            return frames

        optimized = []
        current_frame = frames[0]

        for i in range(1, len(frames)):
            next_frame = frames[i]

            # Merge very short frames with the same viseme
            if (
                current_frame.viseme == next_frame.viseme
                and current_frame.duration < min_duration
            ):
                current_frame.duration += next_frame.duration
            else:
                # Add current frame if it meets minimum duration
                if current_frame.duration >= min_duration:
                    optimized.append(current_frame)
                current_frame = next_frame

        # Add the last frame
        if current_frame.duration >= min_duration:
            optimized.append(current_frame)

        return optimized

    def generate_animation_keyframes(
        self, lipsync_data: LipsyncData
    ) -> List[Dict[str, Any]]:
        """
        Generate animation keyframes for avatar mouth animation.

        Args:
            lipsync_data: Lipsync data with viseme timing

        Returns:
            List of animation keyframes with timing and viseme data
        """
        keyframes = []

        for frame in lipsync_data.frames:
            keyframe = {
                "time": frame.start_time,
                "duration": frame.duration,
                "viseme": frame.viseme.value,
                "confidence": frame.confidence,
                "slot_states": {"Mouth": {"viseme": frame.viseme.value}},
            }
            keyframes.append(keyframe)

        return keyframes


class EmotionModulator:
    """Modulates lipsync animation based on emotional parameters."""

    def __init__(self):
        """Initialize emotion modulator."""
        pass

    def apply_emotion_modulation(
        self,
        lipsync_data: LipsyncData,
        valence: float = 0.0,
        arousal: float = 0.0,
        emotion: str = "neutral",
    ) -> LipsyncData:
        """
        Apply emotional modulation to lipsync data.

        Args:
            lipsync_data: Base lipsync data
            valence: Emotional valence (-1.0 to 1.0, negative=sad, positive=happy)
            arousal: Emotional arousal (0.0 to 1.0, low=calm, high=excited)
            emotion: Named emotion

        Returns:
            Modulated lipsync data
        """
        modulated_frames = []

        for frame in lipsync_data.frames:
            modulated_frame = VisemeFrame(
                viseme=frame.viseme,
                start_time=frame.start_time,
                duration=frame.duration,
                confidence=frame.confidence,
            )

            # Apply emotion-based modifications
            if valence > 0.5:  # Happy/positive
                # Slightly extend vowel sounds for more expression
                if frame.viseme in [VisemeType.AI, VisemeType.E, VisemeType.O]:
                    modulated_frame.duration *= 1.1

            elif valence < -0.5:  # Sad/negative
                # Slightly compress sounds for subdued effect
                modulated_frame.duration *= 0.9

            if arousal > 0.7:  # High arousal/excited
                # Faster speech, shorter pauses
                if frame.viseme == VisemeType.REST:
                    modulated_frame.duration *= 0.7

            modulated_frames.append(modulated_frame)

        return LipsyncData(
            frames=modulated_frames,
            duration=lipsync_data.duration,
            sample_rate=lipsync_data.sample_rate,
        )
