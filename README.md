# ACC (Academic Calendar Core)

A simple Flask API for parsing academic text to extract course codes, keywords, deadlines, and dates, plus task management.

## Features

- **Parse Academic Text**: Extract course codes, keywords, and dates from WhatsApp messages, emails, etc.
- **Task Management**: Create, read, update, and delete tasks via API
- **Smart Date Parsing**: Handles ISO format, natural language, and relative dates
- **Batch Processing**: Parse multiple texts at once
- **RESTful API**: Clean, simple endpoints

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Run

```bash
python app.py
```

Server starts at `http://localhost:5000`

### 3. Use

```bash
# Parse text
curl -X POST http://localhost:5000/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "CSC101 assignment due Oct 15 2025 at 11:59pm"}'

# Create task from text
curl -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Assignment", "text": "CSC101 assignment due Oct 15 2025 at 11:59pm"}'

# Get all tasks
curl http://localhost:5000/tasks
```

## API Endpoints

### Parse Text

**POST /parse**
```json
{
  "text": "CSC101 assignment due Oct 15 2025 at 11:59pm"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "original_text": "CSC101 assignment due Oct 15 2025 at 11:59pm",
    "courses": ["CSC101"],
    "keywords": ["assignment", "due"],
    "deadline_phrase": "due Oct 15 2025 at 11:59pm",
    "datetime_iso": "2025-10-15T23:59:00+00:00",
    "parser_used": "parsedatetime"
  }
}
```

### Parse Batch

**POST /parse/batch**
```json
{
  "texts": [
    "CSC101 exam tomorrow",
    "MATH201 assignment due Friday"
  ]
}
```

### Task Management

**Create Task**
```bash
POST /tasks
{
  "title": "Assignment",
  "description": "Complete homework",
  "text": "CSC101 assignment due Oct 15"  # Optional: auto-parses dates
}
```

**Get All Tasks**
```bash
GET /tasks
GET /tasks?status=pending  # Filter by status
```

**Get Task**
```bash
GET /tasks/<id>
```

**Update Task**
```bash
PUT /tasks/<id>
{
  "title": "New title",
  "status": "completed"
}
```

**Delete Task**
```bash
DELETE /tasks/<id>
```

**Complete Task**
```bash
POST /tasks/<id>/complete
```

## Use as Module

```python
from acc_core import parse_dates_from_text

result = parse_dates_from_text("CSC101 exam Oct 15 at 2pm")
print(result['courses'])      # ['CSC101']
print(result['datetime_iso']) # '2025-10-15T14:00:00+00:00'
```

## Examples

### Real WhatsApp Examples

**Example 1: Zoom Meeting**
```
Topic: CE 382 HCI GROUP PRESENTATION
Time: Sep 16, 2025 12:00 PM
```
→ Detects: CE 382, HCI, presentation, date

**Example 2: Quiz Announcement**
```
Wednesday - DSA, 12noon at the Software Lab
Thursday - OS, Immediately after the Exams
```
→ Detects: DSA, OS, exam, lab, dates

**Example 3: Assignment**
```
For those who missed the C# assignment submission,
submit your work today at her office.
```
→ Detects: assignment, submission, submit, today

### API Integration

```bash
# Send WhatsApp message to API
curl -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "DSA Quiz", "text": "Wednesday - DSA, 12noon at the Software Lab"}'

# Response: Task created with parsed date!
```

### Get Pending Tasks

```bash
curl http://localhost:5000/tasks?status=pending
```

### Mark Task Complete

```bash
curl -X POST http://localhost:5000/tasks/1/complete
```

## Date Formats Supported

- **ISO**: `2025-10-15`, `2025-10-15T14:30`
- **Natural**: "next Monday", "tomorrow", "in 3 days"
- **Traditional**: "Oct 15 2025", "10/15/25"
- **Times**: "at 3pm", "at 14:30", "by 11:59pm"

## Course Code Detection

**Patterns Supported:**
- Standard: CSC101, MATH201, ENG102
- With Spaces: CE 382, CS 101, IT 201
- Abbreviations: DSA, OS, HCI, AI, ML, DB, OOP, DBMS, IOT, etc.

**Examples:**
- ✅ "CE 382 HCI presentation" → ['CE 382', 'HCI']
- ✅ "DSA and OS exams" → ['DSA', 'OS']
- ✅ "CSC101 assignment" → ['CSC101']

## Keywords Detected

**Assessments:** exam, test, quiz, midterm, final, assessment  
**Work:** assignment, homework, project, lab, practical, tutorial  
**Submissions:** submission, submit, due, deadline, hand in, turn in  
**Events:** meeting, presentation, seminar, lecture, class, session  
**Grading:** grade, marked, graded, result, score  
**General:** course, subject, module

## Database

Tasks stored in `tasks.db` (SQLite) in the same directory.

## Project Structure

```
ACC/
├── acc_core.py      # Core parsing module
├── app.py           # Flask API (all endpoints)
├── requirements.txt # Dependencies
├── README.md        # This file
└── tasks.db         # SQLite database (auto-created)
```

## Development

Run in debug mode:
```bash
python app.py
```

Access API at `http://localhost:5000`

## License

MIT
