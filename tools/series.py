import logging
import re

from config.conf import VIDEO_ROOT

logger = logging.getLogger(__name__)


def list_series() -> list[dict]:
    """
    Return a structured list of available TV series with seasons and episode counts.
    """

    series_list: list[dict] = []

    if not VIDEO_ROOT.exists():
        logger.warning("VIDEO_ROOT does not exist: %s", VIDEO_ROOT)
        return series_list

    for series_dir in VIDEO_ROOT.iterdir():
        if not series_dir.is_dir():
            continue

        series_name = series_dir.name
        detected_series_id = None
        seasons_data = []

        for season_dir in series_dir.iterdir():
            if not season_dir.is_dir():
                continue

            season_match = re.match(r"s(\d+)", season_dir.name.lower())
            if not season_match:
                continue

            season_number = int(season_match.group(1))
            episode_count = 0

            for file in season_dir.iterdir():
                if not file.is_file():
                    continue

                match = re.match(
                    r"^([a-zA-Z0-9]+)-s\d+-e\d+\.[^.]+$",
                    file.name,
                    re.IGNORECASE,
                )

                if match:
                    episode_count += 1

                    # détecte le series_id une seule fois
                    if not detected_series_id:
                        detected_series_id = match.group(1).lower()

            if episode_count > 0:
                seasons_data.append(
                    {
                        "season_number": season_number,
                        "episode_count": episode_count,
                    }
                )

        if detected_series_id and seasons_data:
            series_list.append(
                {
                    "series_id": detected_series_id,
                    "series_name": series_name,
                    "aliases": [series_name.replace("-", " ")],
                    "seasons": sorted(seasons_data, key=lambda x: x["season_number"]),
                }
            )

    result = sorted(series_list, key=lambda x: x["series_name"].lower())

    logger.info("Found %d series", len(result))

    return result