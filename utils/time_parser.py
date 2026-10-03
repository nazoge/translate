import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import pytz


RELATIVE_PATTERN = re.compile(
    r"^(?:(?P<weeks>\d+)w)?(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$"
)

DATETIME_PATTERNS = [
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M",
    "%m/%d %H:%M",
    "%m-%d %H:%M",
    "%H:%M",
]


def parse_relative_time(time_str: str) -> Optional[timedelta]:
    match = RELATIVE_PATTERN.match(time_str.strip().lower())
    if not match or not any(match.groupdict().values()):
        return None

    parts = {k: int(v or 0) for k, v in match.groupdict().items()}
    return timedelta(**parts)


def parse_absolute_time(
    time_str: str, tz: pytz.BaseTzInfo
) -> Optional[datetime]:
    time_str = time_str.strip()
    now = datetime.now(tz)

    for pattern in DATETIME_PATTERNS:
        try:
            parsed = datetime.strptime(time_str, pattern)
            if pattern == "%H:%M":
                parsed = parsed.replace(
                    year=now.year, month=now.month, day=now.day
                )
            else:
                parsed = parsed.replace(year=now.year if parsed.year < 100 else parsed.year)
            localized = tz.localize(parsed)
            if localized <= now:
                localized += timedelta(days=1)
            return localized
        except ValueError:
            continue
    return None


def parse_time(
    time_str: str, timezone_str: str = "Asia/Tokyo"
) -> datetime:
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        raise ValueError("❌ 無効なタイムゾーンです")

    relative = parse_relative_time(time_str)
    if relative is not None:
        if relative.total_seconds() <= 0:
            raise ValueError("❌ 時間は1秒以上にしてください")
        return datetime.now(tz) + relative

    absolute = parse_absolute_time(time_str, tz)
    if absolute is not None:
        if absolute <= datetime.now(tz):
            raise ValueError("❌ 過去の日時は指定できません")
        return absolute

    raise ValueError("❌ 時間の形式が正しくありません")


def parse_interval(interval_str: Optional[str]) -> Optional[timedelta]:
    if not interval_str:
        return None
    interval = parse_relative_time(interval_str)
    if interval is None:
        raise ValueError("❌ 繰り返し間隔の形式が正しくありません")
    if interval.total_seconds() < 60:
        raise ValueError("❌ 繰り返し間隔は1分以上にしてください")
    return interval


def format_datetime(dt: datetime, timezone_str: str = "Asia/Tokyo") -> str:
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        tz = pytz.timezone("Asia/Tokyo")
    localized = dt.astimezone(tz)
    return localized.strftime("%Y/%m/%d %H:%M")


def format_interval(interval: Optional[timedelta]) -> str:
    if interval is None:
        return ""
    total = int(interval.total_seconds())
    weeks, remainder = divmod(total, 604800)
    days, remainder = divmod(remainder, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if weeks:
        parts.append(f"{weeks}週間")
    if days:
        parts.append(f"{days}日")
    if hours:
        parts.append(f"{hours}時間")
    if minutes:
        parts.append(f"{minutes}分")
    if seconds:
        parts.append(f"{seconds}秒")
    return "".join(parts) + "ごと"
