from __future__ import annotations

import math
from typing import Any

import numpy as np


_EPSILON = 1e-9


def _mono_or_channels(audio: np.ndarray) -> np.ndarray:
    arr = np.asarray(audio, dtype=np.float32)
    if arr.ndim == 0:
        return arr.reshape(1)
    return arr


def _clip_audio(audio: np.ndarray) -> np.ndarray:
    return np.clip(audio, -1.0, 1.0).astype(np.float32, copy=False)


def _process_channels(audio: np.ndarray, fn) -> np.ndarray:
    arr = _mono_or_channels(audio)
    if arr.ndim == 1:
        return fn(arr)
    processed = [fn(arr[:, ch]) for ch in range(arr.shape[1])]
    min_len = min(len(ch) for ch in processed)
    return np.stack([ch[:min_len] for ch in processed], axis=1)


def peak_normalize(audio: np.ndarray, target_db: float = -1.0) -> np.ndarray:
    arr = _mono_or_channels(audio)
    peak = float(np.max(np.abs(arr))) if arr.size else 0.0
    if peak < _EPSILON:
        return arr.astype(np.float32, copy=False)
    target = 10.0 ** (target_db / 20.0)
    return _clip_audio(arr * (target / peak))


def apply_gain_db(audio: np.ndarray, gain_db: float) -> np.ndarray:
    if abs(gain_db) < 0.01:
        return _mono_or_channels(audio)
    gain = 10.0 ** (gain_db / 20.0)
    return _clip_audio(_mono_or_channels(audio) * gain)


def linear_resample(audio: np.ndarray, factor: float) -> np.ndarray:
    """Simple dependency-free resampler. factor > 1 shortens/raises pitch."""
    factor = max(0.25, min(float(factor), 4.0))
    if abs(factor - 1.0) < 0.001:
        return _mono_or_channels(audio)

    def _one_channel(x: np.ndarray) -> np.ndarray:
        if len(x) < 2:
            return x.astype(np.float32, copy=False)
        new_len = max(2, int(round(len(x) / factor)))
        old_positions = np.arange(len(x), dtype=np.float32)
        new_positions = np.linspace(0, len(x) - 1, new_len, dtype=np.float32)
        return np.interp(new_positions, old_positions, x).astype(np.float32)

    return _process_channels(audio, _one_channel)


def apply_echo(audio: np.ndarray, sample_rate: int, delay_ms: int = 220, decay: float = 0.28) -> np.ndarray:
    delay = max(1, int(sample_rate * max(1, delay_ms) / 1000.0))
    decay = max(0.0, min(float(decay), 0.95))

    def _one_channel(x: np.ndarray) -> np.ndarray:
        y = np.zeros(len(x) + delay, dtype=np.float32)
        y[: len(x)] += x
        y[delay : delay + len(x)] += x * decay
        return _clip_audio(y)

    return _process_channels(audio, _one_channel)


def apply_chorus(
    audio: np.ndarray,
    sample_rate: int,
    mix: float = 0.35,
    base_delay_ms: float = 18.0,
    depth_ms: float = 8.0,
    rate_hz: float = 0.28,
) -> np.ndarray:
    mix = max(0.0, min(float(mix), 1.0))
    base_delay = sample_rate * max(1.0, float(base_delay_ms)) / 1000.0
    depth = sample_rate * max(0.0, float(depth_ms)) / 1000.0
    rate_hz = max(0.02, min(float(rate_hz), 8.0))

    def _one_channel(x: np.ndarray) -> np.ndarray:
        if len(x) < 4:
            return x.astype(np.float32, copy=False)
        idx = np.arange(len(x), dtype=np.float32)
        mod_a = base_delay + depth * np.sin(2.0 * math.pi * rate_hz * idx / sample_rate)
        mod_b = (base_delay * 1.37) + (depth * 0.73) * np.sin(
            2.0 * math.pi * rate_hz * 1.61 * idx / sample_rate + 1.7
        )
        positions_a = idx - mod_a
        positions_b = idx - mod_b
        delayed_a = np.interp(positions_a, idx, x, left=0.0, right=0.0).astype(np.float32)
        delayed_b = np.interp(positions_b, idx, x, left=0.0, right=0.0).astype(np.float32)
        wet = (delayed_a + delayed_b) * 0.5
        return _clip_audio(x * (1.0 - mix) + wet * mix)

    return _process_channels(audio, _one_channel)


def apply_tremolo(audio: np.ndarray, sample_rate: int, rate_hz: float = 5.0, depth: float = 0.45) -> np.ndarray:
    arr = _mono_or_channels(audio)
    rate_hz = max(0.05, min(float(rate_hz), 25.0))
    depth = max(0.0, min(float(depth), 1.0))
    idx = np.arange(arr.shape[0], dtype=np.float32)
    lfo = 1.0 - depth * 0.5 + depth * 0.5 * np.sin(2.0 * math.pi * rate_hz * idx / sample_rate)
    if arr.ndim == 2:
        lfo = lfo[:, None]
    return _clip_audio(arr * lfo)


def apply_robot_vocoder(audio: np.ndarray, sample_rate: int, carrier_hz: float = 90.0, mix: float = 0.65) -> np.ndarray:
    """Lightweight robot/vocoder-like coloration without external DSP dependencies."""
    arr = _mono_or_channels(audio)
    carrier_hz = max(20.0, min(float(carrier_hz), 420.0))
    mix = max(0.0, min(float(mix), 1.0))
    idx = np.arange(arr.shape[0], dtype=np.float32)
    carrier = np.sin(2.0 * math.pi * carrier_hz * idx / sample_rate)
    carrier += 0.35 * np.sin(2.0 * math.pi * carrier_hz * 2.01 * idx / sample_rate)
    carrier = carrier.astype(np.float32)
    if arr.ndim == 2:
        carrier = carrier[:, None]
    rectified = np.abs(arr)
    robotic = rectified * carrier
    return _clip_audio(arr * (1.0 - mix) + robotic * mix * 1.25)


def apply_bitcrusher(audio: np.ndarray, bits: int = 10, hold_samples: int = 1) -> np.ndarray:
    arr = _mono_or_channels(audio)
    bits = max(4, min(int(bits), 16))
    hold_samples = max(1, min(int(hold_samples), 32))
    levels = float((2 ** bits) - 1)
    crushed = np.round((arr + 1.0) * 0.5 * levels) / levels * 2.0 - 1.0
    if hold_samples > 1 and len(crushed) > hold_samples:
        held = crushed.copy()
        held[hold_samples:] = held[(np.arange(hold_samples, len(held)) // hold_samples) * hold_samples]
        crushed = held
    return _clip_audio(crushed)


def apply_audio_effects(audio: np.ndarray, sample_rate: int, config: dict[str, Any] | None) -> np.ndarray:
    if not config or not config.get("audio_effects_enabled", False):
        return _mono_or_channels(audio)

    out = _mono_or_channels(audio)

    pitch_semitones = float(config.get("pitch_shift_semitones", 0.0) or 0.0)
    speed_factor = float(config.get("speed_factor", 1.0) or 1.0)
    if abs(pitch_semitones) >= 0.05:
        out = linear_resample(out, 2.0 ** (pitch_semitones / 12.0))
    if abs(speed_factor - 1.0) >= 0.01:
        out = linear_resample(out, speed_factor)

    if config.get("chorus_enabled", False):
        out = apply_chorus(
            out,
            sample_rate,
            mix=float(config.get("chorus_mix", 0.35) or 0.35),
            depth_ms=float(config.get("chorus_depth_ms", 8.0) or 8.0),
            rate_hz=float(config.get("chorus_rate_hz", 0.28) or 0.28),
        )

    if config.get("echo_enabled", False):
        out = apply_echo(
            out,
            sample_rate,
            delay_ms=int(config.get("echo_delay_ms", 220) or 220),
            decay=float(config.get("echo_decay", 0.28) or 0.28),
        )

    if config.get("robot_enabled", False):
        out = apply_robot_vocoder(
            out,
            sample_rate,
            carrier_hz=float(config.get("robot_carrier_hz", 90.0) or 90.0),
            mix=float(config.get("robot_mix", 0.65) or 0.65),
        )

    if config.get("tremolo_enabled", False):
        out = apply_tremolo(
            out,
            sample_rate,
            rate_hz=float(config.get("tremolo_rate_hz", 5.0) or 5.0),
            depth=float(config.get("tremolo_depth", 0.45) or 0.45),
        )

    if config.get("bitcrusher_enabled", False):
        out = apply_bitcrusher(
            out,
            bits=int(config.get("bitcrusher_bits", 10) or 10),
            hold_samples=int(config.get("bitcrusher_hold", 1) or 1),
        )

    out = apply_gain_db(out, float(config.get("output_gain_db", 0.0) or 0.0))
    if config.get("normalize_audio", True):
        out = peak_normalize(out, target_db=float(config.get("normalize_target_db", -1.0) or -1.0))
    return _clip_audio(out)
