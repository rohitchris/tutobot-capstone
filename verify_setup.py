"""
TutoBot Setup Verification Script
Tests Google Workspace API access and service account configuration
"""

import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def check_service_account():
    """Verify service account JSON exists and is valid"""
    print("🔍 Checking service account configuration...")
    
    if not os.path.exists('config/service_account.json'):
        print("❌ Service account JSON not found at config/service_account.json")
        print("   Please download from Google Cloud Console and place it there.")
        return False
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            'config/service_account.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        print(f"✅ Service account loaded: {creds.service_account_email}")
        return True
    except Exception as e:
        print(f"❌ Error loading service account: {e}")
        return False


def check_sheets_api(spreadsheet_id):
    """Test Google Sheets API access"""
    print("\n🔍 Testing Google Sheets API access...")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            'config/service_account.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=creds)
        
        # Try to read from the spreadsheet
        result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        print(f"✅ Successfully accessed spreadsheet: {result.get('properties', {}).get('title', 'Unknown')}")
        
        # List sheets
        sheets = result.get('sheets', [])
        print(f"   Found {len(sheets)} sheet(s):")
        for sheet in sheets:
            sheet_title = sheet.get('properties', {}).get('title', 'Unknown')
            print(f"   - {sheet_title}")
        
        return True
        
    except HttpError as e:
        if e.resp.status == 404:
            print(f"❌ Spreadsheet not found (ID: {spreadsheet_id})")
            print("   Check the spreadsheet ID from the URL")
        elif e.resp.status == 403:
            print(f"❌ Permission denied")
            print("   Make sure you shared the spreadsheet with:")
            creds = service_account.Credentials.from_service_account_file('config/service_account.json')
            print(f"   {creds.service_account_email}")
        else:
            print(f"❌ Error accessing Sheets API: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_docs_api():
    """Test Google Docs API access"""
    print("\n🔍 Testing Google Docs API access...")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            'config/service_account.json',
            scopes=['https://www.googleapis.com/auth/documents']
        )
        
        service = build('docs', 'v1', credentials=creds)
        print("✅ Google Docs API accessible")
        return True
        
    except Exception as e:
        print(f"❌ Error accessing Docs API: {e}")
        print("   Make sure Google Docs API is enabled in Cloud Console")
        return False


def check_forms_api():
    """Test Google Forms API access"""
    print("\n🔍 Testing Google Forms API access...")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            'config/service_account.json',
            scopes=['https://www.googleapis.com/auth/forms.body']
        )
        
        service = build('forms', 'v1', credentials=creds)
        print("✅ Google Forms API accessible")
        return True
        
    except Exception as e:
        print(f"❌ Error accessing Forms API: {e}")
        print("   Make sure Google Forms API is enabled in Cloud Console")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           TutoBot Setup Verification Script                  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check service account
    if not check_service_account():
        print("\n❌ Setup incomplete. Please fix the service account configuration.")
        sys.exit(1)
    
    # Get spreadsheet ID from user
    print("\n📋 Please provide your Google Spreadsheet ID")
    print("   (Find it in the URL: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit)")
    spreadsheet_id = input("Spreadsheet ID: ").strip()
    
    if not spreadsheet_id:
        print("❌ No spreadsheet ID provided. Skipping Sheets test.")
        sheets_ok = False
    else:
        sheets_ok = check_sheets_api(spreadsheet_id)
    
    # Check other APIs
    docs_ok = check_docs_api()
    forms_ok = check_forms_api()
    
    # Summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    print(f"Service Account:  {'✅ OK' if check_service_account() else '❌ FAIL'}")
    print(f"Google Sheets:    {'✅ OK' if sheets_ok else '❌ FAIL'}")
    print(f"Google Docs:      {'✅ OK' if docs_ok else '❌ FAIL'}")
    print(f"Google Forms:     {'✅ OK' if forms_ok else '❌ FAIL'}")
    print("="*60)
    
    if sheets_ok and docs_ok and forms_ok:
        print("\n🎉 All systems operational! You're ready to run TutoBot.")
        print("\nNext steps:")
        print("1. Ensure your spreadsheet has the required sheets (see README.md)")
        print("2. Run: python main.py --mode planner --spreadsheet-id YOUR_ID --board SSC --grade 5 --subject Mathematics --weeks 4")
    else:
        print("\n⚠️  Some checks failed. Please review the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure all APIs are enabled in Google Cloud Console")
        print("2. Share your spreadsheet with the service account email")
        print("3. Wait 1-2 minutes after enabling APIs")


if __name__ == "__main__":
    main()
