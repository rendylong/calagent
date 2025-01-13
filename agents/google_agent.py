from typing import List, Dict
from tools.google_tools import GoogleTools, create_google_tools

class GoogleAgent:
    """处理 Gmail 和 Calendar 相关任务的 Agent"""
    
    def __init__(self):
        self.google_tools = GoogleTools()
    
    def check_recent_emails(self, max_results: int = 5) -> str:
        """检查最近的邮件并生成摘要报告"""
        try:
            emails = self.google_tools.list_recent_emails(max_results=max_results)
            
            if not emails:
                return "未找到任何邮件。"
            
            report = "**最近邮件摘要报告**\n\n"
            report += "1. **重要邮件列表**\n"
            
            for email in emails:
                report += f"- 主题: {email['subject']}\n"
                report += f"  发件人: {email['sender']}\n"
                report += f"  日期: {email['date']}\n"
                report += f"  摘要: {email['snippet'][:100]}...\n\n"
            
            return report
            
        except Exception as e:
            return f"获取邮件时出错: {str(e)}"
    
    def check_upcoming_events(self, max_results: int = 5) -> str:
        """检查即将到来的日历事件并生成提醒"""
        try:
            events = self.google_tools.list_upcoming_events(max_results=max_results)
            
            if not events:
                return "未找到任何即将到来的事件。"
            
            report = "**即将到来的日历事件**\n\n"
            
            for event in events:
                report += f"- 标题: {event['summary']}\n"
                report += f"  开始时间: {event['start']}\n"
                report += f"  结束时间: {event['end']}\n"
                if event.get('location'):
                    report += f"  地点: {event['location']}\n"
                if event.get('description'):
                    report += f"  描述: {event['description']}\n"
                report += "\n"
            
            return report
            
        except Exception as e:
            return f"获取日历事件时出错: {str(e)}"
    
    def schedule_event(
        self,
        summary: str,
        description: str,
        start_time: str,
        end_time: str,
        location: str = None
    ) -> str:
        """创建新的日历事件"""
        try:
            # 先检查是否有时间冲突
            events = self.google_tools.list_upcoming_events(max_results=5)
            has_conflict = False
            
            for event in events:
                if (event['start'] <= end_time and event['end'] >= start_time):
                    has_conflict = True
                    return f"警告：该时间段与现有事件 '{event['summary']}' 有冲突。"
            
            if not has_conflict:
                result = self.google_tools.create_calendar_event(
                    summary=summary,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    location=location
                )
                
                if result:
                    return f"成功创建事件：{summary}"
                else:
                    return "创建事件失败，请重试。"
                    
        except Exception as e:
            return f"创建事件时出错: {str(e)}"
    
    def daily_summary(self) -> str:
        """生成每日邮件和日历摘要"""
        try:
            email_summary = self.check_recent_emails(max_results=5)
            calendar_summary = self.check_upcoming_events(max_results=5)
            
            report = "**每日摘要报告**\n\n"
            report += "=== 最新邮件 ===\n"
            report += email_summary + "\n\n"
            report += "=== 日历事件 ===\n"
            report += calendar_summary
            
            return report
            
        except Exception as e:
            return f"生成每日摘要时出错: {str(e)}" 