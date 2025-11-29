# TutoBot - AI Lesson Planning Agent

**Automated curriculum planning, lesson design, and assessment creation for Indian educators**

Built with Google ADK (Agent Development Kit) + Gemini 2.5 Flash

---

## Architecture

**4 Specialized Generator Agents:**
1. **Planner Agent** → Creates multi-week curriculum aligned with SSC/CBSE/ICSE/IGCSE
2. **Lesson Agent** → Designs detailed daily lessons with activities
3. **Assessment Agent** → Generates auto-graded quizzes in Google Forms
4. **Export Agent** → Formats and organizes final materials

**1 Universal Quality Assurance Agent:**
5. **Evaluator Agent** → Validates content quality and provides feedback for revisions

**Orchestration:** Sequential pipeline with evaluation loops and shared state via Google Sheets

**Quality Control:** Each generator agent undergoes evaluation with automatic revision cycles (max 3 iterations, quality threshold: 75/100)

**Tools:** Google Sheets, Docs, Forms, Drive + NCERT content search

---

## Prerequisites

1. **Python 3.10+**
2. **Google Cloud Project** with enabled APIs:
   - Google Sheets API
   - Google Docs API
   - Google Forms API
   - Google Drive API
3. **Service Account** with JSON key
4. **Google Sheet** (shared with service account email)
5. **Google Drive Folder** (shared with service account email for document storage)

---

## Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable these APIs (search in top bar):
   - Google Sheets API
   - Google Docs API
   - Google Forms API
   - Google Drive API
4. Create a **Service Account**:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name it `tutobot-agent`
   - Click "Create and Continue"
   - Skip role assignment (click "Continue")
   - Click "Done"
5. Generate JSON key:
   - Click on the service account
   - Go to "Keys" tab
   - Add Key → Create New Key → JSON
   - Download the JSON file

### Step 3: Place Service Account Key

```bash
mkdir -p config
mv ~/Downloads/your-service-account-key.json config/service_account.json
```

### Step 4: Create Google Sheet

1. Create a new Google Sheet: [sheets.google.com](https://sheets.google.com)
2. Note the Spreadsheet ID (from URL):
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
   ```
3. Share the sheet with your service account email:
   - Click "Share" button
   - Add the service account email (found in JSON file: `client_email`)
   - Give "Editor" access

### Step 5: Create Google Drive Folder

1. Create a new folder in Google Drive for storing generated documents
2. Note the Folder ID (from URL):
   ```
   https://drive.google.com/drive/folders/FOLDER_ID
   ```
3. Share the folder with your service account email:
   - Click "Share" button
   - Add the service account email
   - Give "Editor" access

### Step 6: Create Required Sheets

In your Google Spreadsheet, create these sheets (tabs):

- `form_responses` (columns: timestamp, teacher_id, subject, grade, learning_goals, classes_per_week, student_needs)
- `students` (columns: student_id, name, grade, learning_pace, special_needs)
- `curriculum_plan` (columns: week_number, subject, learning_objectives, topics, ncert_references)
- `lesson_plans` (columns: lesson_id, week_number, class_date, duration_minutes, lesson_content, gdocs_link)
- `assessments` (columns: assessment_id, week_number, type, gform_link, answer_key, max_score)
- `student_scores` (columns: student_id, assessment_id, score, timestamp, feedback)
- `final_materials` (columns: material_type, week_topic, link, status)

### Step 7: Run the verification script

```bash
python verify_setup.py
```

Expected output:
```
- Service account loaded
- Successfully accessed spreadsheet
- Google Docs API accessible
- Google Forms API accessible
```

---

## Usage

### Run Planner Agent Only (Test)

```bash
python test.py --mode planner --spreadsheet-id "YOUR_SPREADSHEET_ID" --folder-id "YOUR_FOLDER_ID" \
  --board SSC --grade 5 --subject "Mathematics" --weeks 4 --goals "Master fractions and decimals"
```

### Run Lesson Agent Only (Test)

```bash
python test.py --mode lesson --spreadsheet-id "YOUR_SPREADSHEET_ID" --folder-id "YOUR_FOLDER_ID" \
  --board SSC --grade 5 --subject "Mathematics" --weeks 2 --goals "Master fractions"
```

### Run Full Pipeline (All Agents)

```bash
python test.py --mode full --spreadsheet-id "YOUR_SPREADSHEET_ID" --folder-id "YOUR_FOLDER_ID" \
  --board CBSE --grade 8 --subject "Science" --weeks 6 --goals "Understand cell structure and functions"
```

**Note:** The full pipeline currently processes the first 2 weeks only for demonstration purposes.

---

## Project Structure

```
tutobot-capstone/
├── agents.py              # All 5 agents + orchestration
├── prompts.py             # Prompts for the agents
├── test.py                # Sample scenarios
├── tools.py               # Google Workspace & NCERT tools
├── verify_setup.py        # Google Cloud setup verification script
├── requirements.txt       # Python dependencies
├── config/
│   └── service_account.json  # Google Cloud credentials template
└── README.md              # This file
```

---

## Supported Education Boards

- **SSC** (State Secondary Certificate) - Maharashtra
- **CBSE** (Central Board of Secondary Education)
- **ICSE** (Indian Certificate of Secondary Education)
- **IGCSE** (International General Certificate of Secondary Education)

---

## NCERT Content

Currently includes mock data for:
- Grade 5 Mathematics (Fractions, Decimals)
- Grade 5 Science (Plants)

**To expand:** Edit `NCERT_CONTENT_DB` in `tools.py` with more chapters/topics.

**Future enhancement:** Integrate with NCERT PDF scraping or vector database.

---

## Troubleshooting

### Error: "Service account credentials not found"
- Ensure `config/service_account.json` exists
- Check file permissions

### Error: "Insufficient permissions"
- Share Google Sheet with service account email
- Share Google Drive folder with service account email
- Give "Editor" access for both

### Error: "API not enabled"
- Enable all required APIs in Google Cloud Console
- Wait 1-2 minutes for propagation

### Error: "Invalid spreadsheet ID" or "Invalid folder ID"
- Check the IDs from URLs
- Ensure resources are accessible

### Error: "JSON parse error"
- This indicates the agent output couldn't be parsed
- Check the raw output in console logs
- May require prompt refinement

---

## Roadmap

- [ ] Finalise integration with Google Workspace (Forms, Docs, Drive)
- [ ] Vector database for semantic NCERT search

---

## License

Educational use only. NCERT content belongs to respective copyright holders.

### Technology Stack

- **Framework:** Google ADK (Agent Development Kit)
- **LLM:** Gemini 2.5 Flash
- **Memory:** Google Sheets (shared state)
- **Output:** Google Docs + Forms
- **Auth:** Service Account (automated)
- **Language:** Python 3.10+

---

## API Rate Limits

Be aware of Google API quotas:
- **Sheets API:** 100 requests per 100 seconds per user
- **Docs API:** 60 requests per minute per user
- **Forms API:** 60 requests per minute per user
- **Drive API:** 1,000 requests per 100 seconds per user

---

## Demo

```bash
# Quick test with sample data
python test.py --mode planner --spreadsheet-id "1ABC...XYZ" --folder-id "1DEF...GHI" \
  --board SSC --grade 5 --subject Mathematics --weeks 2 --goals "Master fractions and decimals"
```

Expected output:
1. Curriculum plan written to Sheet
2. NCERT references included
3. Week-by-week breakdown
4. Console output showing agent reasoning and evaluation

---
