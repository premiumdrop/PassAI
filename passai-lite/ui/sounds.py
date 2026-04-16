"""
PassAI Lite — Sound System

Typing sounds (play_tick, play_click) use in-memory WAV synthesis for
instant, low-latency feedback during PIN entry.

Confirmation sounds (unlock, error) play MP3 files from the sounds/ folder
via Windows MCI.  Volume is kept soft (~320/1000).
"""

import ctypes
import io
import math
import struct
import threading
import wave
from pathlib import Path

# ── WAV synthesis for typing sounds ──────────────────────────────────────────

_RATE = 44100


def _synth_wav(freq: float, ms: int, vol: float = 0.18,
               attack_ms: int = 3, release_ms: int = 20) -> bytes:
    """Return a complete RIFF/WAV file as bytes (in-memory, no disk I/O)."""
    n       = int(_RATE * ms / 1000)
    att_n   = min(n, int(_RATE * attack_ms  / 1000))
    rel_n   = min(n, int(_RATE * release_ms / 1000))
    sus_end = n - rel_n

    frames = []
    for i in range(n):
        if i < att_n:
            env = i / att_n if att_n > 0 else 1.0
        elif i >= sus_end:
            env = (n - i) / rel_n if rel_n > 0 else 0.0
        else:
            env = 1.0
        s = int(env * vol * 32767 * math.sin(2.0 * math.pi * freq * i / _RATE))
        frames.append(struct.pack('<h', max(-32767, min(32767, s))))

    pcm = b''.join(frames)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()


# Pre-generate at import time — no disk I/O, <1 ms
_TICK_WAV  = _synth_wav(1046, 26, vol=0.13, attack_ms=2, release_ms=18)
_CLICK_WAV = _synth_wav(880,  32, vol=0.14, attack_ms=3, release_ms=22)


def _play_wav(data: bytes) -> None:
    """Play a pre-built WAV (bytes) asynchronously via winsound SND_MEMORY."""
    def _run():
        try:
            import winsound
            winsound.PlaySound(
                data,
                winsound.SND_MEMORY | winsound.SND_NODEFAULT,
            )
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()


# ── MCI MP3 playback for confirmation / action sounds ────────────────────────

_SOUNDS_DIR = Path(__file__).parent.parent / "sounds"

_FILES = {
    "success": "new-password-edit.mp3",
    "error":   "wrong-pin-password.mp3",
    "copy":    "notification.mp3",
    "unlock":  "correct-pin-only.mp3",
    "delete":  "click.mp3",
    "open":    "notification.mp3",
    "close":   "click.mp3",
}

_VOLUME = 320          # 0-1000 MCI scale — kept soft
_alias_counter = 0
_alias_lock    = threading.Lock()


def _next_alias() -> str:
    global _alias_counter
    with _alias_lock:
        _alias_counter += 1
        return f"passai_{_alias_counter}"


def _play_mp3(key: str) -> None:
    filename = _FILES.get(key)
    if not filename:
        return
    path = _SOUNDS_DIR / filename
    if not path.exists():
        return

    winmm = ctypes.windll.winmm
    alias = _next_alias()
    file_str = str(path).replace("/", "\\")

    def _run():
        try:
            winmm.mciSendStringW(
                f'open "{file_str}" type mpegvideo alias {alias}',
                None, 0, None,
            )
            winmm.mciSendStringW(
                f"setaudio {alias} volume to {_VOLUME}",
                None, 0, None,
            )
            winmm.mciSendStringW(f"play {alias} wait", None, 0, None)
        finally:
            try:
                winmm.mciSendStringW(f"close {alias}", None, 0, None)
            except Exception:
                pass

    threading.Thread(target=_run, daemon=True).start()


# ── Public API ────────────────────────────────────────────────────────────────

# Typing — instant WAV synthesis (soft, no MP3 latency)
def play_tick():  _play_wav(_TICK_WAV)    # PIN digit keypress
def play_click(): _play_wav(_CLICK_WAV)   # PIN backspace / UI click

# Confirmations — MP3 files via MCI
def play_success():      _play_mp3("success")
def play_error():        _play_mp3("error")
def play_copy():         _play_mp3("copy")
def play_unlock():       _play_mp3("unlock")
def play_delete():       _play_mp3("delete")
def play_dialog_open():  _play_mp3("open")
def play_dialog_close(): _play_mp3("close")
