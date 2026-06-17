"""Standbild-Extraktion aus Videodateien für den Kontrollbericht.

Nutzt das portable ffmpeg aus ``imageio-ffmpeg``, sodass keine systemweite
ffmpeg-Installation nötig ist. Pro Video wird ein repräsentatives Standbild
als JPEG gespeichert und kann anschließend als Belegfoto in den Bericht
eingebettet werden.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import imageio_ffmpeg


def get_video_duration(video_path: Path) -> float:
    """Ermittelt die Länge eines Videos in Sekunden.

    Args:
        video_path: Pfad zur Videodatei.

    Returns:
        Dauer des Videos in Sekunden (0.0, falls nicht ermittelbar).
    """
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    # ffmpeg gibt die Dauer auf stderr aus; wir parsen die "Duration:"-Zeile.
    result = subprocess.run(
        [ffmpeg, "-i", str(video_path)],
        capture_output=True,
        text=True,
    )
    for line in result.stderr.splitlines():
        line = line.strip()
        if line.startswith("Duration:"):
            timestamp = line.split("Duration:")[1].split(",")[0].strip()
            try:
                hours, minutes, seconds = timestamp.split(":")
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            except ValueError:
                return 0.0
    return 0.0


def extract_frame(
    video_path: Path,
    output_path: Path,
    timestamp: float | None = None,
) -> Path:
    """Extrahiert ein einzelnes Standbild aus einem Video.

    Args:
        video_path: Pfad zur Videodatei.
        output_path: Zielpfad für das JPEG-Standbild.
        timestamp: Zeitpunkt in Sekunden. Bei ``None`` wird automatisch die
            Mitte des Videos gewählt (oft repräsentativer als der erste Frame).

    Returns:
        Pfad zum erzeugten Standbild.

    Raises:
        RuntimeError: Falls die Extraktion fehlschlägt.
    """
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if timestamp is None:
        duration = get_video_duration(video_path)
        # Mitte des Videos; Fallback auf 0, falls Dauer unbekannt.
        timestamp = duration / 2 if duration > 0 else 0.0

    result = subprocess.run(
        [
            ffmpeg,
            "-y",                     # vorhandene Datei überschreiben
            "-ss", str(timestamp),    # Suchposition (vor -i = schnell)
            "-i", str(video_path),
            "-frames:v", "1",         # genau ein Bild
            "-q:v", "2",              # hohe JPEG-Qualität
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(
            f"Standbild-Extraktion fehlgeschlagen für {video_path}:\n{result.stderr}"
        )
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Standbild aus einem Video extrahieren."
    )
    parser.add_argument("video", type=Path, help="Pfad zur Videodatei")
    parser.add_argument("output", type=Path, help="Zielpfad für das Standbild (JPEG)")
    parser.add_argument(
        "--zeit",
        type=float,
        default=None,
        help="Zeitpunkt in Sekunden (Standard: Mitte des Videos)",
    )
    args = parser.parse_args()

    path = extract_frame(args.video, args.output, args.zeit)
    print(f"Standbild gespeichert: {path}")
