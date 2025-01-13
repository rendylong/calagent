from tools.google_tools import GoogleTools

def test_google_apis():
    try:
        # 初始化 Google Tools
        print("Initializing Google Tools...")
        google_tools = GoogleTools()
        
        # 测试 Gmail API
        print("\nTesting Gmail API...")
        emails = google_tools.list_recent_emails(max_results=3)
        print(f"Successfully retrieved {len(emails)} emails")
        
        # 测试 Calendar API
        print("\nTesting Calendar API...")
        events = google_tools.list_upcoming_events(max_results=3)
        print(f"Successfully retrieved {len(events)} calendar events")
        
        print("\nAll API tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\nError during API testing: {str(e)}")
        return False

if __name__ == "__main__":
    test_google_apis() 