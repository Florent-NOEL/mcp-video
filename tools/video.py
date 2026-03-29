import logging
import re
import subprocess
from pathlib import Path

from config.conf import VIDEO_ROOT, VLC_PATH

logger = logging.getLogger(__name__)


def normalize_series_id(series_id: str) -> str:
    return str(series_id).strip().lower()


def normalize_season_number(season_number: int | str) -> str:
    season_number = str(season_number).strip().lower()

    if season_number.startswith("s"):
        return season_number

    return f"s{season_number}"


def normalize_episode_number(episode_number: int | str) -> str:
    return str(episode_number).strip()


def find_all_series() -> list[dict[str, str]]:
    series_list: list[dict[str, str]] = []

    if not VIDEO_ROOT.exists():
        return series_list

    for series_dir in VIDEO_ROOT.iterdir():
        if not series_dir.is_dir():
            continue

        detected_series_id = None

        for season_dir in series_dir.iterdir():
            if not season_dir.is_dir():
                continue

            for file in season_dir.iterdir():
                if not file.is_file():
                    continue

                match = re.match(r"^([a-zA-Z0-9]+)-s\d+-e\d+\.[^.]+$", file.name, re.IGNORECASE)
                if match:
                    detected_series_id = match.group(1).lower()
                    break

            if detected_series_id:
                break

        if detected_series_id:
            series_list.append(
                {
                    "series_id": detected_series_id,
                    "series_name": series_dir.name,
                    "root_path": str(VIDEO_ROOT),
                }
            )

    return sorted(series_list, key=lambda x: x["series_name"].lower())


def find_series_by_id(series_id: str) -> dict[str, str]:
    normalized_series_id = normalize_series_id(series_id)

    for series in find_all_series():
        if series["series_id"] == normalized_series_id:
            return {
                "series_name": series["series_name"],
                "root_path": series["root_path"],
                "request_status": "found",
            }

    return {
        "series_name": "",
        "root_path": "",
        "request_status": "not_found",
    }


def count_episodes_for_season(
        series_id: str,
        season_folder: str,
        series_name: str,
        root_path: str,
) -> int:
    season_dir = Path(root_path) / series_name / season_folder

    if not season_dir.exists():
        return 0

    pattern = re.compile(
        rf"^{re.escape(series_id)}-{re.escape(season_folder)}-e(\d+)\.[^.]+$",
        re.IGNORECASE,
    )

    count = 0
    for file in season_dir.iterdir():
        if file.is_file() and pattern.match(file.name):
            count += 1

    return count


def find_episode_file(
        series_id: str,
        season_folder: str,
        episode_number: str,
        series_name: str,
        root_path: str,
) -> Path | None:
    season_dir = Path(root_path) / series_name / season_folder

    if not season_dir.exists():
        return None

    pattern = re.compile(
        rf"^{re.escape(series_id)}-{re.escape(season_folder)}-e{re.escape(episode_number)}\.[^.]+$",
        re.IGNORECASE,
    )

    for file in season_dir.iterdir():
        if file.is_file() and pattern.match(file.name):
            return file

    return None


def play_series_episode(
        series_id: str,
        season_number: int | str,
        episode_number: int | str,
) -> str:
    """
    Play a specific TV series episode using VLC.

    Args:
        series_id: Short identifier of the series, for example "gsy"
        season_number: Season number, for example 1
        episode_number: Episode number, for example 3
    """
    normalized_series_id = normalize_series_id(series_id)
    season_folder = normalize_season_number(season_number)
    normalized_episode_number = normalize_episode_number(episode_number)

    logger.info(
        "play_series_episode called with series_id=%s season_number=%s episode_number=%s",
        normalized_series_id,
        season_folder,
        normalized_episode_number,
    )

    if not normalized_series_id or not season_folder or not normalized_episode_number:
        available_series = ", ".join(
            [series["series_id"] for series in find_all_series()]
        )
        return (
            "❌ Missing required parameters.\n"
            "Expected format: series_id, season_number, episode_number\n"
            "Example: gsy, 1, 1\n"
            f"Available series IDs: {available_series}"
        )

    series_info = find_series_by_id(normalized_series_id)
    series_name = series_info["series_name"]
    root_path = series_info["root_path"]
    request_status = series_info["request_status"]

    if request_status != "found":
        return f"❌ Unknown series_id: {normalized_series_id}"

    episode_count = count_episodes_for_season(
        normalized_series_id,
        season_folder,
        series_name,
        root_path,
    )

    if episode_count == 0:
        return f"❌ No episodes found for {series_name} {season_folder}"

    try:
        if int(normalized_episode_number) > episode_count:
            return f"❌ The season has only {episode_count} episodes."
    except ValueError:
        return "❌ episode_number must be a valid number."

    episode_file = find_episode_file(
        normalized_series_id,
        season_folder,
        normalized_episode_number,
        series_name,
        root_path,
    )

    if episode_file is None:
        return (
            f"❌ Episode file not found for "
            f"{normalized_series_id}-{season_folder}-e{normalized_episode_number}"
        )

    if not VLC_PATH.exists():
        return f"❌ VLC not found: {VLC_PATH}"

    try:
        subprocess.Popen([str(VLC_PATH), str(episode_file)])
        logger.info("Launching VLC with file=%s", episode_file)
        return f"✅ Playing: {episode_file}"
    except Exception as e:
        logger.exception("Failed to launch VLC")
        return f"❌ Error: {e}"