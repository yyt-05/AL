# 结合 ReAct 的手段将 deepseek 打造成智能体
import json  # 用于处理 JSON 数据
from llm import client # 用于与 LLM 交互
from prompt import REACT_PROMPT  # 用于获取 ReAct 的提示模板
from tools import get_closing_price, tools  # 导入工具列表


# 定义发送消息的函数
def send_message(messages):
  """
  向 LLM 发送消息并获取响应
  :param message: 要发送的消息内容
  :return: LLM 的响应内容
  """
  response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
  )
  return response


if __name__ == "__main__":  # 主函数入口
  # 设置助手的角色
  instructions = "你是一个股票助手，可以回答股票相关的问题。"
  
  # 假设用户输入的消息
  query = "青岛啤酒和贵州茅台的收盘价哪个更高？"

  # 使用模板构建完整的提示词
  prompt = REACT_PROMPT.format(instructions=instructions,tools=tools, tool_names="get_closing_price", input=query)

  print("Prompt:", prompt)  # 打印提示词以供调试