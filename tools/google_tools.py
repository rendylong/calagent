from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from crewai.tools.structured_tool import CrewStructuredTool
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import pickle
import os
import datetime
import time
from socket import timeout

class GoogleTools:
    """Google API工具类，用于处理Gmail和Calendar相关操作"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/calendar'
    ]
    
    def __init__(self):
        """初始化Google API服务"""
        self.creds = self._authenticate()
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        print("Gmail service initialized!")
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        print("Calendar service initialized!")

    def _authenticate(self) -> Credentials:
        """Google API认证流程"""
        creds = None
        if os.path.exists('token.pickle'):
            print("Loading credentials from token.pickle")
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing credentials")
                creds.refresh(Request())
            else:
                print("Getting new credentials")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                print("Saving credentials to token.pickle")
                pickle.dump(creds, token)

        return creds

    def _execute_with_retry(self, request, max_retries=3):
        """执行API请求，带有重试机制"""
        for attempt in range(max_retries):
            try:
                return request.execute()
            except Exception as e:
                if isinstance(e, HttpError):
                    if e.resp.status in [429, 500, 503]:  # Rate limit or server errors
                        if attempt == max_retries - 1:
                            raise
                        print(f"服务器错误，正在进行第{attempt + 1}次重试...")
                        time.sleep(2 ** attempt)  # 指数退避
                    else:
                        raise
                else:
                    if attempt == max_retries - 1:
                        raise
                    print(f"请求出错，正在进行第{attempt + 1}次重试... 错误: {str(e)}")
                    time.sleep(1)

    def list_recent_emails(self, max_results: int = 5) -> List[Dict[str, str]]:
        """获取最近的邮件列表"""
        try:
            print(f"开始获取最近{max_results}封邮件...")
            
            # 获取邮件ID列表
            request = self.gmail_service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['INBOX']
            )
            results = self._execute_with_retry(request)
            
            messages = results.get('messages', [])
            if not messages:
                print("未找到任何邮件")
                return []
                
            print(f"找到{len(messages)}封邮件，正在获取详细信息...")
            emails = []
            
            for message in messages:
                try:
                    request = self.gmail_service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    )
                    msg = self._execute_with_retry(request)
                    
                    headers = {header['name'].lower(): header['value'] 
                             for header in msg['payload']['headers']}
                    
                    email = {
                        'message_id': msg['id'],
                        'subject': headers.get('subject', 'No Subject'),
                        'sender': headers.get('from', 'Unknown'),
                        'date': headers.get('date', 'Unknown'),
                        'snippet': msg.get('snippet', '')
                    }
                    emails.append(email)
                    print(f"已处理邮件: {email['subject']}")
                    
                except Exception as e:
                    print(f"处理单个邮件时出错: {str(e)}")
                    continue
                    
            print(f"成功获取 {len(emails)} 封邮件")
            return emails
            
        except Exception as e:
            print(f"获取邮件列表时出错: {str(e)}")
            return []

    def list_upcoming_events(self, max_results: int = 10) -> List[Dict[str, str]]:
        """获取未来的日历事件"""
        try:
            print(f"Fetching {max_results} upcoming events...")
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            request = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            )
            events_result = self._execute_with_retry(request)

            events = events_result.get('items', [])
            if not events:
                print("No upcoming events found.")
                return []

            event_list = []
            for event in events:
                calendar_event = {
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'location': event.get('location'),
                    'description': event.get('description')
                }
                event_list.append(calendar_event)
                print(f"Retrieved event: {calendar_event['summary'][:50]}...")

            return event_list

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    def create_calendar_event(
        self,
        summary: str,
        description: str,
        start_time: str,
        end_time: str,
        location: Optional[str] = None
    ) -> Dict[str, str]:
        """创建新的日历事件"""
        try:
            print(f"Creating calendar event: {summary}")
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'Asia/Shanghai'
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'Asia/Shanghai'
                }
            }
            if location:
                event['location'] = location

            request = self.calendar_service.events().insert(
                calendarId='primary',
                body=event
            )
            created_event = self._execute_with_retry(request)

            calendar_event = {
                'id': created_event['id'],
                'summary': created_event['summary'],
                'start': created_event['start']['dateTime'],
                'end': created_event['end']['dateTime'],
                'location': created_event.get('location'),
                'description': created_event.get('description')
            }
            
            print(f"Successfully created event: {calendar_event['summary']}")
            return calendar_event

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return {}

# Input schemas for tools
class ListEmailsInput(BaseModel):
    max_results: int = 5

class ListEventsInput(BaseModel):
    max_results: int = 10

class CreateEventInput(BaseModel):
    summary: str
    description: str
    start_time: str
    end_time: str
    location: Optional[str] = None

# Response models
class EmailMessage(BaseModel):
    sender: str
    subject: str
    date: str
    snippet: str

class CalendarEvent(BaseModel):
    id: str
    summary: str
    start: str
    end: str
    location: Optional[str] = None
    description: Optional[str] = None

def create_calendar_event(
    google_tools: GoogleTools,
    summary: str,
    description: str,
    start_time: str,
    end_time: str,
    location: Optional[str] = None
) -> Dict[str, str]:
    """创建新的日历事件"""
    try:
        print(f"Creating calendar event: {summary}")
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Shanghai'
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Shanghai'
            }
        }
        if location:
            event['location'] = location

        request = google_tools.calendar_service.events().insert(
            calendarId='primary',
            body=event
        )
        created_event = google_tools._execute_with_retry(request)

        calendar_event = {
            'id': created_event['id'],
            'summary': created_event['summary'],
            'start': created_event['start']['dateTime'],
            'end': created_event['end']['dateTime'],
            'location': created_event.get('location'),
            'description': created_event.get('description')
        }
        
        print(f"Successfully created event: {calendar_event['summary']}")
        return calendar_event

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {}

def create_google_tools():
    """Create and return a list of structured tools for Gmail and Calendar operations."""
    google_tools = GoogleTools()
    
    return [
        CrewStructuredTool.from_function(
            func=lambda max_results: list_recent_emails(google_tools, max_results),
            name="list_recent_emails",
            description="获取最近的邮件列表，返回发件人、主题、日期和内容摘要"
        ),
        CrewStructuredTool.from_function(
            func=lambda max_results, time_min=None: list_upcoming_events(google_tools, max_results, time_min),
            name="list_upcoming_events", 
            description="获取未来的日历事件列表，返回事件标题、时间、地点和描述"
        ),
        CrewStructuredTool.from_function(
            func=lambda summary, description, start_time, end_time, location=None: create_calendar_event(
                google_tools, summary, description, start_time, end_time, location
            ),
            name="create_calendar_event",
            description="创建新的日历事件，需要提供事件标题、描述、开始时间、结束时间和地点（可选）"
        )
    ] 