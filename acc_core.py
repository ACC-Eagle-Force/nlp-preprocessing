"""
Academic Calendar Core (ACC) Module - Robust Rewrite

A robust parser for extracting course codes, keywords, deadlines, and dates
from academic-related text strings, with special handling for WhatsApp messages
and complex date contexts.

Author: ACC Team
Version: 3.0.0
License: MIT
"""

import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple

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

# ============================================================================
# CONFIGURATION
# ============================================================================

# Course code patterns
COURSE_CODE_RE = re.compile(r'\b([A-Z]{2,4}\s?\d{2,3})\b')
COURSE_ABBREVIATIONS = {
    'DSA', 'OS', 'HCI', 'AI', 'ML', 'DB', 'DM', 'SE', 'CN', 'TOC', 
    'DBMS', 'OOP', 'DS', 'NLP', 'CV', 'RL', 'GIS', 'CAD', 'IOT', 'IR'
}

# Course name pattern (e.g., "Environmental Management", "Data Structures")
COURSE_NAME_RE = re.compile(
    r'\b([A-Z][a-z]+(?:\s+(?:and\s+)?[A-Z][a-z]+){1,3})\s+'
    r'(?:assignment|exam|quiz|project|course|class|module|test|lab|homework)',
    re.IGNORECASE
)

# Academic keywords
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

# Deadline trigger words
DEADLINE_TRIGGERS = ['deadline', 'due', 'submit', 'submission', 'hand in']

# parsedatetime calendar
_pdt_cal = pdt.Calendar()

# Date exclusion patterns (months, days that confuse parsers)
EXCLUDE_PATTERNS = {
    'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 
    'SEP', 'OCT', 'NOV', 'DEC', 'MON', 'TUE', 'WED', 'THU', 
    'FRI', 'SAT', 'SUN', 'AM', 'PM', 'GMT', 'UTC'
}


# ============================================================================
# TEXT PREPROCESSING
# ============================================================================

def clean_whatsapp_format(text: str) -> str:
    """
    Remove WhatsApp message formatting artifacts.
    
    Handles:
    - [10/24/25, 3:45 PM] John Doe: message
    - John Doe, [10/24/25 3:45 PM] message
    - Forwarded message metadata
    
    Args:
        text: Raw WhatsApp message text
        
    Returns:
        Cleaned text without WhatsApp formatting
    """
    if not text:
        return text
    
    # Remove WhatsApp timestamp and sender patterns
    patterns = [
        r'^\[[\d/]+,?\s+[\d:]+\s*[APM]{2}\]\s*[^:]+:\s*',  # [10/24/25, 3:45 PM] Name:
        r'^[^,]+,\s*\[[\d/]+\s+[\d:]+\s*[APM]{2}\]\s*',     # Name, [10/24/25 3:45 PM]
        r'^\[[\d/]+,?\s+[\d:]+\]\s*[^:]+:\s*',              # [10/24/25, 3:45] Name:
        r'^Forwarded message.*?:\s*',                       # Forwarded message:
        r'^\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}\s*[APM]{2}\s*-\s*[^:]+:\s*'  # 10/24/25, 3:45 PM - Name:
    ]
    
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    return cleaned.strip()


def normalize_text(text: str) -> str:
    """
    Normalize text for better parsing.
    
    - Remove extra whitespace
    - Normalize quotes
    - Fix common typos
    """
    if not text:
        return text
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    return text.strip()


# ============================================================================
# COURSE CODE EXTRACTION
# ============================================================================

def extract_course_codes(text: str) -> List[str]:
    """
    Extract course codes and course names from text.
    
    Extracts:
    - Standard codes: CSC101, MATH201, CE 382
    - Abbreviations: DSA, OS, HCI (as whole words)
    - Full names: "Environmental Management", "Data Structures"
    
    Args:
        text: Input text
        
    Returns:
        List of unique course identifiers
    """
    if not text or not isinstance(text, str):
        logger.warning(f"Invalid input to extract_course_codes: {text}")
        return []
    
    try:
        courses = []
        text_upper = text.upper()
        
        # 1. Extract standard course codes (CSC101, CE 382)
        standard_codes = COURSE_CODE_RE.findall(text_upper)
        for code in standard_codes:
            # Normalize spacing (CE 382 -> CE382 or keep as is)
            normalized = code.replace(' ', '')
            # Filter out date-like patterns (SEP16, OCT24)
            prefix = normalized[:3]
            if prefix not in EXCLUDE_PATTERNS:
                courses.append(code)
        
        # 2. Extract course abbreviations (only whole words)
        words = re.findall(r'\b[A-Z]{2,5}\b', text_upper)
        for word in words:
            if word in COURSE_ABBREVIATIONS and word not in courses:
                courses.append(word)
        
        # 3. Extract full course names (Environmental Management, etc.)
        course_names = COURSE_NAME_RE.findall(text)
        for name in course_names:
            # Clean up the name
            name_clean = name.strip()
            if name_clean and name_clean not in courses:
                courses.append(name_clean)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_courses = []
        for course in courses:
            course_key = course.upper().replace(' ', '')
            if course_key not in seen:
                seen.add(course_key)
                unique_courses.append(course)
        
        return unique_courses
        
    except Exception as e:
        logger.error(f"Error extracting course codes: {e}", exc_info=True)
        return []


# ============================================================================
# KEYWORD EXTRACTION
# ============================================================================

def extract_keywords(text: str) -> List[str]:
    """
    Extract academic keywords from text.
    
    Args:
        text: Input text
        
    Returns:
        List of found keywords (deduplicated)
    """
    if not text or not isinstance(text, str):
        return []
    
    try:
        text_lower = text.lower()
        found = []
        seen = set()
        
        for keyword in KEYWORDS:
            if keyword in text_lower and keyword not in seen:
                found.append(keyword)
                seen.add(keyword)
        
        return found
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}", exc_info=True)
        return []


# ============================================================================
# DEADLINE PHRASE EXTRACTION
# ============================================================================

def extract_deadline_context(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract deadline phrase and focused date context.
    
    Returns both:
    1. Full deadline phrase (for context)
    2. Focused date string (for parsing)
    
    Args:
        text: Input text
        
    Returns:
        Tuple of (full_deadline_phrase, focused_date_string)
    """
    if not text or not isinstance(text, str):
        return None, None
    
    try:
        # Build pattern from deadline triggers
        triggers = '|'.join(DEADLINE_TRIGGERS)
        
        # Match deadline phrase (up to 150 chars after trigger)
        pattern = rf'({triggers})[^.!?\n]{{0,150}}'
        match = re.search(pattern, text, flags=re.IGNORECASE)
        
        if not match:
            return None, None
        
        full_phrase = match.group(0)
        
        # Extract FOCUSED date context (after the trigger word)
        # This removes confusing prior context like "month of February 2025"
        trigger_word = match.group(1)
        after_trigger = full_phrase.split(trigger_word, 1)[1] if trigger_word in full_phrase else full_phrase
        
        # Look for time/date indicators in the focused part
        focused_indicators = [
            r'\b\d{1,2}:\d{2}\s*[ap]m\b',           # 11:59pm
            r'\b(?:today|tonight|tomorrow)\b',       # today, tomorrow
            r'\b(?:this|next)\s+\w+\b',              # this Friday, next week
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',   # 28/02/2025
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4}\b',  # 28 Feb 2025
            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b'  # Friday
        ]
        
        # Find the earliest date/time indicator
        earliest_pos = len(after_trigger)
        earliest_match = None
        
        for indicator_pattern in focused_indicators:
            match_obj = re.search(indicator_pattern, after_trigger, flags=re.IGNORECASE)
            if match_obj and match_obj.start() < earliest_pos:
                earliest_pos = match_obj.start()
                earliest_match = match_obj
        
        if earliest_match:
            # Extract from the earliest indicator to end of phrase
            focused_text = after_trigger[earliest_pos:]
            # Limit to reasonable length (first 100 chars after indicator)
            focused_text = focused_text[:100]
            return full_phrase, focused_text.strip()
        
        # Fallback: use text after trigger
        return full_phrase, after_trigger.strip()[:100]
        
    except Exception as e:
        logger.error(f"Error extracting deadline context: {e}", exc_info=True)
        return None, None


# ============================================================================
# DATE PARSING
# ============================================================================

def parse_with_dateparser(text: str, settings: Optional[Dict[str, Any]] = None) -> Optional[datetime]:
    """
    Parse date using dateparser with smart settings.
    """
    if not text:
        return None
    
    if settings is None:
        settings = {
            "PREFER_DATES_FROM": "future",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "TO_TIMEZONE": "UTC",
            "RELATIVE_BASE": datetime.now(tz=tz.tzlocal()),
            "STRICT_PARSING": False
        }
    
    try:
        dt = dateparser.parse(text, settings=settings)
        return dt
    except Exception as e:
        logger.debug(f"dateparser failed for '{text}': {e}")
        return None


def parse_with_parsedatetime(text: str) -> Optional[datetime]:
    """
    Parse date using parsedatetime as fallback.
    """
    if not text:
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


def extract_explicit_date(text: str) -> Optional[datetime]:
    """
    Extract explicit date formats (ISO, common formats).
    Fast path for well-formatted dates.
    """
    if not text:
        return None
    
    patterns = [
        # ISO formats
        (r'\b(\d{4}-\d{2}-\d{2}(?:T|\s)\d{2}:\d{2}(?::\d{2})?)\b', "%Y-%m-%d %H:%M"),
        (r'\b(\d{4}-\d{2}-\d{2})\b', "%Y-%m-%d"),
        # Common formats
        (r'\b(\d{1,2}/\d{1,2}/\d{4})\b', "%d/%m/%Y"),
        (r'\b(\d{1,2}-\d{1,2}-\d{4})\b', "%d-%m-%Y"),
    ]
    
    for pattern, date_format in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                # Use dateparser for robust parsing
                dt = parse_with_dateparser(match.group(1))
                if dt:
                    return dt
            except Exception as e:
                logger.debug(f"Failed to parse explicit date: {e}")
                continue
    
    return None


def parse_date_smart(text: str, deadline_focused: Optional[str] = None) -> Tuple[Optional[datetime], str]:
    """
    Smart multi-strategy date parsing.
    
    Priority:
    1. Deadline-focused text (if provided)
    2. Explicit date formats
    3. Full text with dateparser
    4. Fallback to parsedatetime
    
    Args:
        text: Full text
        deadline_focused: Focused deadline date string
        
    Returns:
        Tuple of (parsed_datetime, parser_name)
    """
    # Strategy 1: Parse from deadline-focused text first
    if deadline_focused:
        logger.info(f"Attempting to parse deadline-focused text: '{deadline_focused}'")
        
        # Try explicit date first
        dt = extract_explicit_date(deadline_focused)
        if dt:
            return dt, "deadline-explicit"
        
        # Try dateparser
        dt = parse_with_dateparser(deadline_focused)
        if dt:
            return dt, "deadline-dateparser"
        
        # Try parsedatetime
        dt = parse_with_parsedatetime(deadline_focused)
        if dt:
            return dt, "deadline-parsedatetime"
    
    # Strategy 2: Look for explicit dates in full text
    dt = extract_explicit_date(text)
    if dt:
        return dt, "explicit-format"
    
    # Strategy 3: Use dateparser on full text (risky but necessary)
    dt = parse_with_dateparser(text)
    if dt:
        return dt, "dateparser-full"
    
    # Strategy 4: Last resort - parsedatetime
    dt = parse_with_parsedatetime(text)
    if dt:
        return dt, "parsedatetime-full"
    
    return None, "none"


# ============================================================================
# MAIN PARSING FUNCTION
# ============================================================================

def parse_dates_from_text(text: str) -> Dict[str, Any]:
    """
    Robust combined parsing pipeline.
    
    Extracts:
    - Course codes (standard + full names)
    - Academic keywords
    - Deadline phrases
    - Dates (with smart multi-strategy parsing)
    
    Args:
        text: Input academic text
        
    Returns:
        Dictionary with all extracted information
    """
    # Input validation
    if not text:
        logger.warning("Empty text provided")
        return {
            "original_text": text,
            "cleaned_text": "",
            "courses": [],
            "keywords": [],
            "deadline_phrase": None,
            "deadline_focused": None,
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
            "cleaned_text": str(text),
            "courses": [],
            "keywords": [],
            "deadline_phrase": None,
            "deadline_focused": None,
            "datetime_utc": None,
            "datetime_iso": None,
            "parser_used": None,
            "error": error_msg
        }
    
    try:
        # Preprocess text
        cleaned = clean_whatsapp_format(text)
        cleaned = normalize_text(cleaned)
        
        logger.info(f"Processing text: '{text[:100]}...'")
        logger.info(f"Cleaned text: '{cleaned[:100]}...'")
        
        # Extract deadline context
        deadline_phrase, deadline_focused = extract_deadline_context(cleaned)
        
        # Initialize result
        result = {
            "original_text": text,
            "cleaned_text": cleaned,
            "courses": extract_course_codes(cleaned),
            "keywords": extract_keywords(cleaned),
            "deadline_phrase": deadline_phrase,
            "deadline_focused": deadline_focused,
            "datetime_utc": None,
            "datetime_iso": None,
            "parser_used": None
        }
        
        # Parse date using smart strategy
        dt, parser_name = parse_date_smart(cleaned, deadline_focused)
        
        if dt:
            # Ensure UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            
            result.update({
                "datetime_utc": dt,
                "datetime_iso": dt.isoformat(),
                "parser_used": parser_name
            })
            
            logger.info(f"Successfully parsed date: {dt.isoformat()} (parser: {parser_name})")
        else:
            logger.info("No date found in text")
        
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            "original_text": text,
            "cleaned_text": text,
            "courses": [],
            "keywords": [],
            "deadline_phrase": None,
            "deadline_focused": None,
            "datetime_utc": None,
            "datetime_iso": None,
            "parser_used": None,
            "error": error_msg
        }


# ============================================================================
# TEST FUNCTION
# ============================================================================

def main():
    """Test the parser with various inputs."""
    test_cases = [
        "Good afternoon Ladies and Gentlemen Kindly note that today ends the month of February 2025 and the deadline for the Environmental Management assignment is 11:59pm today Thank you",
        "[10/24/25, 3:45 PM] John: CSC101 assignment due by 5 Oct 2025 at 11:59pm",
        "DSA project submission before Friday at midnight",
        "Machine Learning exam on 2025-11-15 at 2:00pm",
        "Submit Data Structures homework by tomorrow 5pm",
        "CE 382 quiz next Monday",
        "Final exam for Operating Systems course is on 12/12/25 at 9am"
    ]
    
    print("=" * 80)
    print("ACC CORE - ROBUST PARSER TEST")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}")
        print(f"{'='*80}")
        print(f"Input: {test}")
        print(f"{'-'*80}")
        
        result = parse_dates_from_text(test)
        
        print(f"Cleaned: {result['cleaned_text']}")
        print(f"Courses: {result['courses']}")
        print(f"Keywords: {result['keywords']}")
        print(f"Deadline Phrase: {result['deadline_phrase']}")
        print(f"Deadline Focused: {result['deadline_focused']}")
        print(f"Parsed Date: {result['datetime_iso']}")
        print(f"Parser Used: {result['parser_used']}")
        if 'error' in result:
            print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()