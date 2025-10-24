# ACC (Academic Calendar Core)

A simple Flask API for parsing academic text to extract course codes, keywords, deadlines, and dates.

## Features

- **Parse Academic Text**: Extract course codes, keywords, and dates from WhatsApp messages, emails, etc.
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

# Parse multiple texts
curl -X POST http://localhost:5000/parse/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["CSC101 exam tomorrow", "MATH201 assignment due Friday"]}'
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
  },
  "timestamp": "2025-10-13T10:30:00+00:00"
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

Response:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "original_text": "CSC101 exam tomorrow",
        "courses": ["CSC101"],
        "keywords": ["exam"],
        "datetime_iso": "2025-10-14T00:00:00+00:00",
        "parser_used": "dateparser"
      },
      {
        "original_text": "MATH201 assignment due Friday",
        "courses": ["MATH201"],
        "keywords": ["assignment", "due"],
        "datetime_iso": "2025-10-17T00:00:00+00:00",
        "parser_used": "dateparser"
      }
    ],
    "count": 2
  },
  "timestamp": "2025-10-13T10:30:00+00:00"
}
```

### Health Check

**GET /health**
```json
{
  "status": "healthy",
  "service": "ACC API",
  "timestamp": "2025-10-13T10:30:00+00:00"
}
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
# Parse WhatsApp message
curl -X POST http://localhost:5000/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Wednesday - DSA, 12noon at the Software Lab"}'

# Response: Parsed data with course codes, keywords, and date!
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

## Project Structure

```
ACC/
├── acc_core.py      # Core parsing module
├── app.py           # Flask API (parsing endpoints only)
├── requirements.txt  # Dependencies
├── Procfile         # Render deployment configuration
├── runtime.txt      # Python version specification
├── .gitignore       # Git ignore rules
└── README.md        # This file
```

## Development

Run in debug mode:
```bash
python app.py
```

Access API at `http://localhost:5000`

## Deployment to Render

### Prerequisites
- GitHub repository with your code
- Render account (free tier available)

### Steps

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create a new Web Service on Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

3. **Configure the service**
   - **Name**: `acc-api` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (or upgrade as needed)

4. **Environment Variables** (optional)
   - `FLASK_ENV`: `production` (for production mode)
   - `PORT`: Automatically set by Render

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your API

### Your API will be available at:
```
https://your-app-name.onrender.com
```

### Test your deployed API:
```bash
curl -X POST https://your-app-name.onrender.com/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "CSC101 assignment due tomorrow"}'
```

### Files for Render Deployment

The following files are included for successful deployment:

- `Procfile` - Tells Render how to run your app
- `runtime.txt` - Specifies Python version
- `requirements.txt` - Lists all dependencies including gunicorn
- `.gitignore` - Excludes unnecessary files from git

## License

MIT