"""
Academic Calendar Core (ACC) Module

A robust parser for extracting course codes, keywords, deadlines, and dates
from academic-related text strings.

Author: ACC Team
License: MIT
"""

import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

try:
    import dateparser
    import parsedatetime as pdt
    from dateutil import tz
except ImportError as e:
    raise ImportError(
        f"Required dependencies not installed: {e}. "
        "Please install with: pip install dateparser parsedatetime python-dateutil"
    )

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuration constants
# Enhanced course code pattern to match:
# - Standard: CSC101, MATH201
# - With spaces: CE 382, CS 101  
# - Abbreviations: DSA, OS, HCI (only as standalone words)
COURSE_RE = re.compile(r'\b([A-Z]{2,4}\s\d{2,3}|[A-Z]{2,4}\d{2,3})\b')  # Main pattern
COURSE_ABBREVIATIONS = {
    'DSA', 'OS', 'HCI', 'AI', 'ML', 'DB', 'DM', 'SE', 'CN', 'TOC', 
    'DBMS', 'OOP', 'DS', 'NLP', 'CV', 'RL', 'GIS', 'CAD', 'IOT'
}

# Comprehensive university keywords
KEYWORDS = [
    # Assessments
    "exam", "test", "quiz", "midterm", "final", "assessment",
    # Work
    "assignment", "homework", "project", "lab", "practical", "tutorial",
    # Submissions
    "submission", "submit", "due", "deadline", "hand in", "turn in",
    # Events
    "meeting", "presentation", "seminar", "lecture", "class", "session",
    # Grading
    "grade", "marked", "graded", "result", "score",
    # General
    "course", "subject", "module"
]

# parsedatetime calendar (single instance for efficiency)
_pdt_cal = pdt.Calendar()


def parse_date_with_dateparser(text: str, settings: Optional[Dict[str, Any]] = None) -> Optional[datetime]:
    """
    Parse date using dateparser library.
    
    Args:
        text: Input text containing potential date information
        settings: Optional dateparser settings dictionary
        
    Returns:
        Timezone-aware datetime object in UTC or None if parsing fails
        
    Example:
        >>> parse_date_with_dateparser("next Monday at 3pm")
        datetime.datetime(2025, 10, 13, 15, 0, tzinfo=datetime.timezone.utc)
    """
    if not text or not isinstance(text, str):
        logger.warning(f"Invalid input to parse_date_with_dateparser: {text}")
        return None
        
    if settings is None:
        settings = {
            "PREFER_DATES_FROM": "future",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "TO_TIMEZONE": "UTC",
            "RELATIVE_BASE": datetime.now(tz=tz.tzlocal())
        }
    
    try:
        dt = dateparser.parse(text, settings=settings)
        return dt
    except Exception as e:
        logger.debug(f"dateparser failed for '{text}': {e}")
        return None


def parse_date_with_parsedatetime(text: str) -> Optional[datetime]:
    """
    Fallback date parser using parsedatetime library.
    
    Args:
        text: Input text containing potential date information
        
    Returns:
        Timezone-aware datetime object in UTC or None if parsing fails
        
    Example:
        >>> parse_date_with_parsedatetime("tomorrow at 5pm")
        datetime.datetime(2025, 10, 13, 17, 0, tzinfo=datetime.timezone.utc)
    """
    if not text or not isinstance(text, str):
        logger.warning(f"Invalid input to parse_date_with_parsedatetime: {text}")
        return None
    
    try:
        now = datetime.now(tz=tz.tzlocal())
        time_struct, parse_status = _pdt_cal.parseDT(datetimeString=text, tzinfo=now.tzinfo)
        
        if parse_status:
            return time_struct.astimezone(timezone.utc)
        return None
    except Exception as e:
        logger.debug(f"parsedatetime failed for '{text}': {e}")
        return None


def extract_course_codes(text: str) -> List[str]:
    """
    Extract course codes from text (e.g., CSC101, MATH201, CE 382, DSA).
    
    Args:
        text: Input text to search for course codes
        
    Returns:
        List of found course codes
        
    Example:
        >>> extract_course_codes("CSC101 and MATH201 exams")
        ['CSC101', 'MATH201']
        >>> extract_course_codes("CE 382 HCI presentation")
        ['CE 382', 'HCI']
    """
    if not text or not isinstance(text, str):
        logger.warning(f"Invalid input to extract_course_codes: {text}")
        return []
    
    try:
        text_upper = text.upper()
        courses = []
        
        # Filter out common false positives (month names, etc.)
        EXCLUDE_PATTERNS = {
            'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 
            'SEP', 'OCT', 'NOV', 'DEC', 'MON', 'TUE', 'WED', 'THU', 
            'FRI', 'SAT', 'SUN', 'AM', 'PM', 'GMT', 'UTC'
        }
        
        # Extract standard course codes (e.g., CSC101, CE 382)
        standard_courses = COURSE_RE.findall(text_upper)
        for course in standard_courses:
            # Filter out dates like "SEP 16"
            prefix = course.split()[0] if ' ' in course else course[:3]
            if prefix not in EXCLUDE_PATTERNS:
                courses.append(course)
        
        # Extract abbreviations (only if they appear as whole words)
        words = re.findall(r'\b[A-Z]+\b', text_upper)
        for word in words:
            if word in COURSE_ABBREVIATIONS and word not in courses:
                courses.append(word)
        
        return courses
    except Exception as e:
        logger.error(f"Error extracting course codes: {e}")
        return []


def extract_keywords(text: str) -> List[str]:
    """
    Extract academic keywords from text.
    
    Args:
        text: Input text to search for keywords
        
    Returns:
        List of found keywords
        
    Example:
        >>> extract_keywords("Final exam and assignment due")
        ['exam', 'assignment', 'due', 'final']
    """
    if not text or not isinstance(text, str):
        logger.warning(f"Invalid input to extract_keywords: {text}")
        return []
    
    try:
        text_lower = text.lower()
        found = [k for k in KEYWORDS if k in text_lower]
        return found
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return []


def extract_deadline_phrases(text: str) -> Optional[str]:
    """
    Extract deadline-related phrases from text.
    
    Args:
        text: Input text to search for deadline phrases
        
    Returns:
        First matching deadline phrase or None
        
    Example:
        >>> extract_deadline_phrases("Assignment due by Friday at 11:59pm")
        'due by Friday at 11:59pm'
    """
    if not text or not isinstance(text, str):
        logger.warning(f"Invalid input to extract_deadline_phrases: {text}")
        return None
    
    try:
        pattern = r'(due|deadline|submit (by|before|on)).{0,80}'
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return match.group(0) if match else None
    except Exception as e:
        logger.error(f"Error extracting deadline phrases: {e}")
        return None


def parse_dates_from_text(text: str) -> Dict[str, Any]:
    """
    Combined parsing pipeline to extract all information from academic text.
    
    This function:
    1. Extracts course codes
    2. Identifies academic keywords
    3. Finds deadline phrases
    4. Parses dates using multiple strategies (ISO format, dateparser, parsedatetime)
    
    Args:
        text: Input text containing academic information
        
    Returns:
        Dictionary containing:
            - original_text: The input text
            - courses: List of course codes found
            - keywords: List of academic keywords found
            - deadline_phrase: Extracted deadline phrase (if any)
            - datetime_utc: Parsed datetime object in UTC (if any)
            - datetime_iso: ISO format string of the datetime (if any)
            - parser_used: Name of the parser that succeeded (if any)
            - error: Error message if something went wrong (if any)
            
    Example:
        >>> result = parse_dates_from_text("CSC101 assignment due by 5 Oct 2025 at 11:59pm")
        >>> result['courses']
        ['CSC101']
        >>> result['keywords']
        ['assignment', 'due']
        >>> result['datetime_iso']
        '2025-10-05T23:59:00+00:00'
    """
    # Input validation
    if not text:
        logger.warning("Empty text provided to parse_dates_from_text")
        return {
            "original_text": text,
            "courses": [],
            "keywords": [],
            "deadline_phrase": None,
            "datetime_utc": None,
            "datetime_iso": None,
            "parser_used": None,
            "error": "Empty input text"
        }
    
    if not isinstance(text, str):
        error_msg = f"Invalid input type: expected str, got {type(text).__name__}"
        logger.error(error_msg)
        return {
            "original_text": str(text),
            "courses": [],
            "keywords": [],
            "deadline_phrase": None,
            "datetime_utc": None,
            "datetime_iso": None,
            "parser_used": None,
            "error": error_msg
        }
    
    try:
        # Pre-process text
        t = text.strip()
        
        # Initialize result dictionary
        result = {
            "original_text": text,
            "courses": extract_course_codes(t),
            "keywords": extract_keywords(t),
            "deadline_phrase": extract_deadline_phrases(t),
            "datetime_utc": None,
            "datetime_iso": None,
            "parser_used": None
        }
        
        # Try ISO format first (fast path for explicit dates)
        iso_pattern = r'(\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(:\d{2})?)?)'
        iso_match = re.search(iso_pattern, t)
        
        if iso_match:
            try:
                dt = dateparser.parse(
                    iso_match.group(0),
                    settings={"RETURN_AS_TIMEZONE_AWARE": True, "TO_TIMEZONE": "UTC"}
                )
                if dt:
                    result.update({
                        "datetime_utc": dt,
                        "datetime_iso": dt.isoformat(),
                        "parser_used": "iso-regex+dateparser"
                    })
                    logger.info(f"Successfully parsed date using ISO format: {dt.isoformat()}")
                    return result
            except Exception as e:
                logger.debug(f"ISO format parsing failed: {e}")
        
        # Try dateparser
        dt = parse_date_with_dateparser(t)
        if dt:
            dt_utc = dt.astimezone(timezone.utc)
            result.update({
                "datetime_utc": dt_utc,
                "datetime_iso": dt_utc.isoformat(),
                "parser_used": "dateparser"
            })
            logger.info(f"Successfully parsed date using dateparser: {dt_utc.isoformat()}")
            return result
        
        # Fallback to parsedatetime
        dt = parse_date_with_parsedatetime(t)
        if dt:
            dt_utc = dt.astimezone(timezone.utc)
            result.update({
                "datetime_utc": dt_utc,
                "datetime_iso": dt_utc.isoformat(),
                "parser_used": "parsedatetime"
            })
            logger.info(f"Successfully parsed date using parsedatetime: {dt_utc.isoformat()}")
            return result
        
        # No date found
        logger.info(f"No date found in text: {text}")
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error parsing text: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            "original_text": text,
            "courses": [],
            "keywords": [],
            "deadline_phrase": None,
            "datetime_utc": None,
            "datetime_iso": None,
            "parser_used": None,
            "error": error_msg
        }


def main():
    """Test function with sample inputs."""
    samples = [
        "csc101 assignment due by 5 Oct 2025 at 11:59pm",
        "project meeting next monday 3pm",
        "submit before 2025-10-05",
        "final exam 12/12/25",
        "quiz in 3 days",
        "MATH201 midterm on 2025-11-15 at 2:00pm"
    ]
    
    print("Testing ACC Core Module")
    print("=" * 60)
    
    for sample in samples:
        print(f"\nInput: {sample}")
        result = parse_dates_from_text(sample)
        print(f"Courses: {result['courses']}")
        print(f"Keywords: {result['keywords']}")
        print(f"Deadline: {result['deadline_phrase']}")
        print(f"Date: {result['datetime_iso']}")
        print(f"Parser: {result['parser_used']}")
        if 'error' in result:
            print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()

