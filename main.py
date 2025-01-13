from datetime import datetime, timedelta
from agents.google_agent import GoogleAgent

def main():
    # 创建 Google Agent
    agent = GoogleAgent()
    
    # 1. 检查最近邮件
    print("\n=== 检查最近邮件 ===")
    email_summary = agent.check_recent_emails(max_results=3)
    print(email_summary)
    
    # 2. 检查日历事件
    print("\n=== 检查即将到来的事件 ===")
    calendar_summary = agent.check_upcoming_events(max_results=3)
    print(calendar_summary)
    
    # 3. 创建测试事件
    print("\n=== 创建测试日历事件 ===")
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    start_time = tomorrow.replace(hour=10, minute=0).strftime("%Y-%m-%dT%H:%M:%S%z")
    end_time = tomorrow.replace(hour=11, minute=0).strftime("%Y-%m-%dT%H:%M:%S%z")
    
    event_result = agent.schedule_event(
        summary="测试会议",
        description="这是一个用于测试的会议",
        start_time=start_time,
        end_time=end_time,
        location="线上会议"
    )
    print(event_result)
    
    # 4. 生成每日摘要
    print("\n=== 生成每日摘要 ===")
    daily_summary = agent.daily_summary()
    print(daily_summary)

if __name__ == "__main__":
    main() 