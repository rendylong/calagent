# CrewAI 项目最佳实践指南

本指南总结了使用 CrewAI 构建 Agent 项目的最佳实践和经验教训。

## 1. 项目结构

推荐的项目结构：
```
project/
├── tools/                # 工具实现目录
│   └── specific_tools.py # 具体工具类
├── agents/              # Agent 实现目录
│   └── specific_agent.py # 具体 Agent 类
├── main.py             # 主程序
├── requirements.txt    # 依赖管理
└── tests/             # 测试目录
    └── test_tools.py  # 工具测试
```

## 2. 工具实现最佳实践

### 2.1 工具类实现

```python
from typing import Dict, List, Optional
import time

class SpecificTools:
    """具体工具类的实现"""
    
    def __init__(self):
        # 初始化必要的服务和客户端
        self.service = self._initialize_service()
    
    def _initialize_service(self):
        """初始化服务的辅助方法"""
        pass
    
    def _execute_with_retry(self, request, max_retries=3):
        """通用的重试机制实现"""
        for attempt in range(max_retries):
            try:
                return request.execute()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"重试 {attempt + 1}/{max_retries}...")
                time.sleep(2 ** attempt)  # 指数退避
    
    def specific_operation(self, param1: str, param2: int) -> Dict[str, str]:
        """具体操作的实现"""
        try:
            # 1. 参数验证
            if not param1 or param2 < 0:
                raise ValueError("Invalid parameters")
            
            # 2. 准备请求
            request = self.service.prepare_request(param1, param2)
            
            # 3. 执行请求（带重试）
            result = self._execute_with_retry(request)
            
            # 4. 处理结果
            return {
                'status': 'success',
                'data': result
            }
            
        except Exception as e:
            print(f"操作失败: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
```

### 2.2 CrewAI 工具包装

```python
from crewai.tools import CrewStructuredTool

def create_tools():
    """创建 CrewAI 工具列表"""
    tools = SpecificTools()
    
    return [
        CrewStructuredTool.from_function(
            func=lambda p1, p2: tools.specific_operation(p1, p2),
            name="specific_operation",
            description="执行特定操作，需要提供参数1和参数2",
            # 保持参数简单，使用基本类型
            parameters={
                "param1": {
                    "type": "string",
                    "description": "第一个参数的描述"
                },
                "param2": {
                    "type": "integer",
                    "description": "第二个参数的描述"
                }
            }
        )
    ]
```

## 3. Agent 实现最佳实践

### 3.1 Agent 类实现

```python
class SpecificAgent:
    """特定功能的 Agent 实现"""
    
    def __init__(self):
        self.tools = SpecificTools()
    
    def execute_task(self, input_data: Dict) -> str:
        """执行具体任务"""
        try:
            # 1. 输入验证
            if not self._validate_input(input_data):
                return "输入数据无效"
            
            # 2. 执行操作
            result = self.tools.specific_operation(
                input_data['param1'],
                input_data['param2']
            )
            
            # 3. 格式化输出
            if result['status'] == 'success':
                return self._format_success_result(result['data'])
            else:
                return f"操作失败: {result['message']}"
                
        except Exception as e:
            return f"任务执行出错: {str(e)}"
    
    def _validate_input(self, input_data: Dict) -> bool:
        """输入验证辅助方法"""
        required_fields = ['param1', 'param2']
        return all(field in input_data for field in required_fields)
    
    def _format_success_result(self, data: Dict) -> str:
        """结果格式化辅助方法"""
        return f"""
        操作成功！
        结果: {data}
        """
```

## 4. LLM 配置最佳实践

```python
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew

def create_crew():
    """创建和配置 Crew"""
    
    # 1. 配置 LLM
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        # 可选：添加其他配置
        request_timeout=30
    )
    
    # 2. 创建 Agent
    agent = Agent(
        role='专家角色',
        goal='明确的目标描述',
        backstory="""详细的背景描述，包括：
        1. Agent 的专长
        2. 行为准则
        3. 工作方式""",
        tools=create_tools(),
        verbose=True
    )
    
    # 3. 创建任务
    task = Task(
        description="""详细的任务描述，包括：
        1. 具体目标
        2. 执行步骤
        3. 预期输出""",
        agent=agent
    )
    
    # 4. 创建 Crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        llm=llm,
        verbose=True
    )
    
    return crew
```

## 5. 测试最佳实践

### 5.1 工具测试

```python
# tests/test_tools.py

def test_specific_operation():
    """测试特定操作"""
    tools = SpecificTools()
    
    # 1. 测试正常情况
    result = tools.specific_operation("test", 1)
    assert result['status'] == 'success'
    
    # 2. 测试错误情况
    result = tools.specific_operation("", -1)
    assert result['status'] == 'error'
```

### 5.2 集成测试

```python
# tests/test_integration.py

def test_agent_with_tools():
    """测试 Agent 和工具的集成"""
    agent = SpecificAgent()
    
    # 1. 准备测试数据
    test_input = {
        'param1': 'test',
        'param2': 1
    }
    
    # 2. 执行测试
    result = agent.execute_task(test_input)
    
    # 3. 验证结果
    assert "操作成功" in result
```

## 6. 常见陷阱和解决方案

1. **工具复杂度过高**
   - ✅ 保持工具功能单一
   - ✅ 使用基本数据类型作为参数
   - ❌ 避免复杂的对象作为参数

2. **错误处理不完善**
   - ✅ 实现重试机制
   - ✅ 提供详细的错误信息
   - ✅ 在每一层都做适当的错误处理

3. **状态管理问题**
   - ✅ 避免使用全局状态
   - ✅ 通过类属性管理状态
   - ✅ 明确状态的生命周期

4. **工具描述不清晰**
   - ✅ 提供详细的工具描述
   - ✅ 说明参数的用途和格式
   - ✅ 给出使用示例

## 7. 调试技巧

1. **启用详细日志**
```python
agent = Agent(
    ...
    verbose=True
)
```

2. **添加调试日志**
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def some_function():
    logger.debug("详细的调试信息")
```

3. **使用断点和异常捕获**
```python
try:
    result = complex_operation()
    logger.debug(f"操作结果: {result}")
except Exception as e:
    logger.error(f"详细错误: {str(e)}", exc_info=True)
```

## 8. 性能优化建议

1. **缓存重复调用**
```python
from functools import lru_cache

class SpecificTools:
    @lru_cache(maxsize=100)
    def expensive_operation(self, param: str):
        # 耗时操作的实现
        pass
```

2. **批量处理**
```python
def batch_process(self, items: List[str], batch_size: int = 10):
    """批量处理数据"""
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        self._process_batch(batch)
```

3. **异步操作**
```python
import asyncio

async def async_operation(self):
    """异步操作实现"""
    tasks = [self._async_task() for _ in range(5)]
    results = await asyncio.gather(*tasks)
    return results
``` 