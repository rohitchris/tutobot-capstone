"""
TutoBot Custom Tools
Integrates with Google Workspace APIs and NCERT content
"""

import json
from typing import Dict, List, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ========== Configuration ==========
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/forms.body',
    # 'https://www.googleapis.com/auth/drive.file'
    'https://www.googleapis.com/auth/drive'
]

class GoogleWorkspaceTools:
    """Unified Google Workspace API client"""
    
    def __init__(self, service_account_file: str):
        self.creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
        self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)
        self.forms_service = build('forms', 'v1', credentials=self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)


# ========== Google Sheets Tools ==========

def sheets_read(spreadsheet_id: str, range_name: str, service_account_file: str = '../service_account.json') -> List[List[Any]]:
    """
    Read data from Google Sheets
    
    Args:
        spreadsheet_id: The Google Sheets ID
        range_name: A1 notation range (e.g., 'Sheet1!A1:D10')
        service_account_file: Path to service account JSON
        
    Returns:
        List of rows, each row is a list of cell values
    """
    try:
        tools = GoogleWorkspaceTools(service_account_file)
        result = tools.sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        return result.get('values', [])
    except HttpError as e:
        print(f"Sheets read error: {e}")
        return []


def sheets_write(spreadsheet_id: str, range_name: str, values: List[List[Any]], service_account_file: str = '../service_account.json') -> bool:
    """
    Write data to Google Sheets (overwrites existing)
    
    Args:
        spreadsheet_id: The Google Sheets ID
        range_name: A1 notation range
        values: 2D list of values to write
        service_account_file: Path to service account JSON
        
    Returns:
        True if successful, False otherwise
    """
    try:
        tools = GoogleWorkspaceTools(service_account_file)
        body = {'values': values}
        tools.sheets_service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption='RAW', body=body).execute()
        return True
    except HttpError as e:
        print(f"Sheets write error: {e}")
        return False


def sheets_append(spreadsheet_id: str, range_name: str, values: List[List[Any]], service_account_file: str = '../service_account.json') -> bool:
    """
    Append data to Google Sheets
    
    Args:
        spreadsheet_id: The Google Sheets ID
        range_name: A1 notation range
        values: 2D list of values to append
        service_account_file: Path to service account JSON
        
    Returns:
        True if successful, False otherwise
    """
    try:
        tools = GoogleWorkspaceTools(service_account_file)
        body = {'values': values}
        tools.sheets_service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='RAW', insertDataOption='INSERT_ROWS', body=body).execute()
        return True
    except HttpError as e:
        print(f"Sheets append error: {e}")
        return False

# ========== NCERT Reference Tool ==========

# Mock NCERT database (in production, this would be a vector DB or indexed content)
NCERT_CONTENT_DB = {
    "5_mathematics_fractions": {
        "grade": 5,
        "subject": "Mathematics",
        "chapter": "Fractions",
        "chapter_number": 7,
        "topics": ["Introduction to Fractions", "Equivalent Fractions", "Adding Fractions", "Subtracting Fractions"],
        "content_summary": "This chapter introduces fractions as parts of a whole, covers equivalent fractions, and basic operations.",
        "key_concepts": [
            "A fraction represents a part of a whole",
            "The numerator indicates parts taken, denominator indicates total parts",
            "Equivalent fractions have the same value but different numerators/denominators"
        ],
        "example_problems": [
            "If you eat 3 out of 8 slices of pizza, what fraction did you eat?",
            "Find three equivalent fractions of 1/2"
        ]
    },
    "5_mathematics_decimals": {
        "grade": 5,
        "subject": "Mathematics",
        "chapter": "Decimals",
        "chapter_number": 8,
        "topics": ["Introduction to Decimals", "Decimal Places", "Comparing Decimals", "Operations with Decimals"],
        "content_summary": "This chapter introduces decimal notation and operations with decimal numbers.",
        "key_concepts": [
            "Decimals are another way to represent fractions",
            "The decimal point separates the whole number from the fractional part",
            "Place value continues to the right of decimal: tenths, hundredths, thousandths"
        ],
        "example_problems": [
            "Write 3/10 as a decimal",
            "Compare 0.5 and 0.05"
        ]
    },
    "5_science_plants": {
        "grade": 5,
        "subject": "Science",
        "chapter": "Plant Life",
        "chapter_number": 5,
        "topics": ["Parts of Plants", "Photosynthesis", "Plant Reproduction", "Importance of Plants"],
        "content_summary": "Study of plant structure, life processes, and their importance in ecosystem.",
        "key_concepts": [
            "Plants have roots, stems, leaves, flowers, and fruits",
            "Photosynthesis is how plants make food using sunlight",
            "Plants reproduce through seeds and spores"
        ],
        "example_problems": [
            "Draw and label the parts of a flowering plant",
            "Explain the process of photosynthesis"
        ]
    }
}


def search_ncert_content(grade: int, subject: str, topic: str) -> Dict[str, Any]:
    """
    Search NCERT content database for relevant educational material
    
    Args:
        grade: Student grade level (1-12)
        subject: Subject name (Mathematics, Science, etc.)
        topic: Topic to search for
        
    Returns:
        Dictionary with chapter information, concepts, and examples
    """
    # Normalize inputs
    subject = subject.lower().strip()
    topic = topic.lower().strip()
    
    # Search through database
    results = []
    for key, content in NCERT_CONTENT_DB.items():
        if (content['grade'] == grade and 
            subject in content['subject'].lower() and
            any(topic in t.lower() for t in content['topics'])):
            results.append(content)
    
    if results:
        # Return the most relevant match
        return results[0]
    else:
        # Return empty structure if no match
        return {
            "grade": grade,
            "subject": subject,
            "chapter": f"Content for {topic} not found in database",
            "topics": [],
            "content_summary": f"Please manually add NCERT content for Grade {grade} {subject} - {topic}",
            "key_concepts": [],
            "example_problems": []
        }


# ========== Google Docs Tool ==========

# '''
def create_google_doc(title: str, content: str, folder_id: Optional[str] = None, service_account_file: str = '../service_account.json') -> str:
    try:
        tools = GoogleWorkspaceTools(service_account_file)

        # 1. Prepare file metadata (Define folder immediately)
        file_metadata = {'name': title, 'mimeType': 'application/vnd.google-apps.document'}
        
        # If a folder is provided, add it to parents immediately
        if folder_id:
            file_metadata['parents'] = [folder_id]

        # 2. Create the file using DRIVE API (Not Docs API)
        # This ensures it is born inside the folder.
        doc = tools.drive_service.files().create(body=file_metadata).execute()
        doc_id = doc.get('id')

        # 3. Insert content (Now we use the Docs API)
        requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
        tools.docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

        return f"https://docs.google.com/document/d/{doc_id}/edit"

    except HttpError as e:
        print(f"Google Docs error: {e}")
        return ""
'''
def create_google_doc(title: str, content: str, folder_id: str, service_account_file: str = '../service_account.json') -> str:
    """
    Create a Google Doc with formatted content
    
    Args:
        title: Document title
        content: Text content to insert
        folder_id: Optional Drive folder ID to store document
        service_account_file: Path to service account JSON
        
    Returns:
        Document URL or empty string on error
    """
    try:
        tools = GoogleWorkspaceTools(service_account_file)
        
        # Create document
        doc = tools.docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc.get('documentId')
        
        # Insert content
        requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
        tools.docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        
        # Move to folder if specified
        if folder_id:
            file = tools.drive_service.files().get(fileId=doc_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents', []))
            tools.drive_service.files().update(fileId=doc_id, addParents=folder_id, removeParents=previous_parents, fields='id, parents').execute()
        
        return f"https://docs.google.com/document/d/{doc_id}/edit"
    
    except HttpError as e:
        print(f"Google Docs error: {e}")
        return ""
'''


# ========== Google Forms Tool ==========

def create_google_form(title: str, questions: List[Dict[str, Any]], 
                       service_account_file: str = '../service_account.json') -> str:
    """
    Create a Google Form with auto-grading quiz
    
    Args:
        title: Form title
        questions: List of question dicts with format:
            {
                'question': 'What is 2+2?',
                'type': 'MULTIPLE_CHOICE',  # or 'SHORT_ANSWER'
                'options': ['2', '3', '4', '5'],
                'correct_answer': '4',
                'points': 1
            }
        service_account_file: Path to service account JSON
        
    Returns:
        Form URL or empty string on error
    """
    try:
        tools = GoogleWorkspaceTools(service_account_file)
        
        # Create form
        form = {"info": {"title": title, "documentTitle": title}}
        result = tools.forms_service.forms().create(body=form).execute()
        form_id = result.get('formId')
        
        # Enable quiz mode
        update_requests = [{"updateSettings": {"settings": {"quizSettings": {"isQuiz": True}}, "updateMask": "quizSettings.isQuiz"}}]
        
        # Add questions
        for i, q in enumerate(questions):
            question_item = {
                "title": q['question'],
                "questionItem": {
                    "question": {
                        "required": True,
                        "grading": {
                            "pointValue": q.get('points', 1),
                            "correctAnswers": {"answers": [{"value": q['correct_answer']}]}
                        }
                    }
                }
            }
            
            if q['type'] == 'MULTIPLE_CHOICE':
                question_item['questionItem']['question']['choiceQuestion'] = {"type": "RADIO", "options": [{"value": opt} for opt in q.get('options', [])]}
            elif q['type'] == 'SHORT_ANSWER':
                question_item['questionItem']['question']['textQuestion'] = {"paragraph": False}
            
            update_requests.append({"createItem": {"item": question_item, "location": {"index": i}}})
        
        # Apply all updates
        tools.forms_service.forms().batchUpdate(formId=form_id, body={"requests": update_requests}).execute()
        
        return f"https://docs.google.com/forms/d/{form_id}/edit"
    
    except HttpError as e:
        print(f"Google Forms error: {e}")
        return ""


# ========== Tool Registry for ADK ==========

def get_all_tools():
    """Return all tools as ADK-compatible FunctionTools"""
    from google.adk.tools import FunctionTool
    
    return [
        FunctionTool(func=sheets_read),
        FunctionTool(func=sheets_write),
        FunctionTool(func=sheets_append),
        FunctionTool(func=search_ncert_content),
        FunctionTool(func=create_google_doc),
        FunctionTool(func=create_google_form),
    ]
