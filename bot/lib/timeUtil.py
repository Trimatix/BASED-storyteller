from datetime import timedelta, datetime
from typing import Dict
import re


def td_format_noYM(td_object: timedelta) -> str:
    """Create a string describing the attributes of a given datetime.timedelta object, in a
    human reader-friendly format.
    This function does not create 'week', 'month' or 'year' strings, its highest time denominator is 'day'.
    Any time denominations that are equal to zero will not be present in the string.

    :param datetime.timedelta td_object: The timedelta to describe
    :return: A string describing td_object's attributes in a human-readable format
    :rtype: str
    """
    seconds = int(td_object.total_seconds())
    periods = [
        ('day', 60 * 60 * 24),
        ('hour', 60 * 60),
        ('minute', 60),
        ('second', 1)
    ]

    strings = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append("%s %s%s" % (period_value, period_name, has_s))

    return ", ".join(strings)


def timeDeltaFromDict(timeDict: dict) -> timedelta:
    """Construct a datetime.timedelta from a dictionary,
    transforming keys into keyword arguments for the timedelta constructor.

    :param dict timeDict: dictionary containing measurements for each time interval. i.e weeks, days, hours, minutes,
                            seconds, microseconds and milliseconds. all are optional and case sensitive.
    :return: a timedelta with all of the attributes requested in the dictionary.
    :rtype: datetime.timedelta
    """
    return timedelta(weeks=timeDict["weeks"] if "weeks" in timeDict else 0,
                     days=timeDict["days"] if "days" in timeDict else 0,
                     hours=timeDict["hours"] if "hours" in timeDict else 0,
                     minutes=timeDict["minutes"] if "minutes" in timeDict else 0,
                     seconds=timeDict["seconds"] if "seconds" in timeDict else 0,
                     microseconds=timeDict["microseconds"] if "microseconds" in timeDict else 0,
                     milliseconds=timeDict["milliseconds"] if "milliseconds" in timeDict else 0)


UTC_OFFSETS = { "Y": timedelta(hours=-12),
                "X": timedelta(hours=-11),
                "W": timedelta(hours=-10),
                "V+": timedelta(hours=-9, minutes=-30),
                "V": timedelta(hours=-9),
                "U": timedelta(hours=-8),
                "T": timedelta(hours=-7),
                "S": timedelta(hours=-6),
                "R": timedelta(hours=-5),
                "Q": timedelta(hours=-4),
                "P+": timedelta(hours=-3, minutes=-30),
                "P": timedelta(hours=-3),
                "O": timedelta(hours=-2),
                "N": timedelta(hours=-1),
                "Z": timedelta(hours=0),
                "A": timedelta(hours=1),
                "B": timedelta(hours=2),
                "C": timedelta(hours=3),
                "C+": timedelta(hours=3, minutes=30),
                "D": timedelta(hours=4),
                "D+": timedelta(hours=4, minutes=30),
                "E": timedelta(hours=5),
                "E+": timedelta(hours=5, minutes=30),
                "E*": timedelta(hours=5, minutes=45),
                "F": timedelta(hours=6),
                "F+": timedelta(hours=3, minutes=30),
                "G": timedelta(hours=7),
                "H": timedelta(hours=8),
                "H+": timedelta(hours=8, minutes=45),
                "I": timedelta(hours=9),
                "I+": timedelta(hours=9, minutes=30),
                "K": timedelta(hours=10),
                "K+": timedelta(hours=10, minutes=30),
                "L": timedelta(hours=11),
                "M": timedelta(hours=12),
                "M*": timedelta(hours=12, minutes=45),
                "M+": timedelta(hours=13),
                "M++": timedelta(hours=14)}

anytime = re.compile("^\\d\\d?:\\d\\d( ?(am|pm))?$")
twelveHour = re.compile("^\\d\\d?:\\d\\d ?(am|pm)$")
twentyFourHour = re.compile("^\\d\\d?:\\d\\d$")

def stringIsTime(s) -> bool:
    return bool(anytime.match(s.lower()))

def parseTime(s) -> datetime:
    if not stringIsTime(s):
        raise ValueError("Not a valid time")
    m = twelveHour.match(s.lower())
    is24 = False
    if m is None:
        m = twentyFourHour.match(s.lower())
        is24 = True
    if m is None:
        raise ValueError("No match")
    
    colonIndex = s.index(":")
    hours = int(s[0:colonIndex])
    minutes = int(s[colonIndex+1:colonIndex+3])

    if minutes < 0 or minutes > 59:
        raise ValueError("Not a valid time")
    if is24:
        if hours < 0 or hours > 23:
            raise ValueError("Not a valid time")
    else:
        if hours < 0 or hours > 11:
            raise ValueError("Not a valid time")

    if not is24:
        dayHalf = s[-2:].lower()
        if dayHalf == "pm":
            if hours == 0:
                raise ValueError("Not a valid time")
            hours += 12

    now = datetime.utcnow()
    return datetime(year=now.year, month=now.month, day=now.day, hour=hours, minute=minutes)


def formatTDHM(td: timedelta) -> str:
    currentSeconds = int(td.total_seconds())
    prefix = "+" if currentSeconds >= 0 else "-"
    currentSeconds = abs(currentSeconds)
    hours = 0
    minutes = 0
    if currentSeconds >= 60 * 60:
        hours, currentSeconds = divmod(currentSeconds, 60 * 60)
    if currentSeconds >= 60:
        minutes, currentSeconds = divmod(currentSeconds, 60)

    return prefix + str(hours).rjust(2, "0") + ":" + str(minutes).rjust(2, "0")
