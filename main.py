import pandas as pd
import requests
import json
from openai import OpenAI

from config import *

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def call_deepseek_api(text):
    """调用DeepSeek API进行文本分析"""
    url = URL
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构造完整提示词
    system_prompt = PROMPT
    
    user_prompt = f"文本内容：{text}\n关键词列表：{KEYWORDS}"
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False
        )
        
        api_response = response.model_dump()
        
        # 验证响应结构
        if not isinstance(api_response.get("choices"), list) or len(api_response["choices"]) == 0:
            raise ValueError("无效的choices字段")
            
        message = api_response["choices"][0].get("message", {})
        content = message.get("content", "").strip()
        print(content)
        
        # 直接解析内容中的数组
        if content.startswith("[") and content.endswith("]"):
            result = json.loads(content)
        else:
            raise ValueError(f"响应内容不是有效数组: {content}")
        
        # 验证结果
        if len(result) != len(KEYWORDS):
            raise ValueError(f"数组长度{len(result)}与关键词数量{len(KEYWORDS)}不匹配")
        if not all(x in (0, 1) for x in result):
            raise ValueError(f"数组包含非0/1值: {result}")
            
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"API请求失败: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {str(e)}")
        print("原始响应:", response.text)
    except ValueError as e:
        print(f"数据验证失败: {str(e)}")
    except Exception as e:
        print(f"未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return [0]*len(KEYWORDS)

def load_column(df, *args):
    text = ""
    for arg in args:
        text += df[arg].fillna('') + " "
    return text

def process_excel():
    """处理Excel文件主函数"""
    # 读取数据
    df = pd.read_excel(INPUT_FILE)
    
    # 拼接文本列,如果不需要拼接就直接输入一个列名
    df["combined_text"] = load_column(df, *TARGET)
    print(df["combined_text"])
    
    # 为每个关键词创建结果列
    for keyword in KEYWORDS:
        df[keyword] = 0
    
    # 处理每一行数据
    for index, row in df.iterrows():
        print(f"Processing row {index+1}/{len(df)}")
        result = call_deepseek_api(row["combined_text"])
        
        # 更新结果列
        for i, val in enumerate(result):
            df.at[index, KEYWORDS[i]] = val
    
    # 保存结果（保留原始格式）
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

if __name__ == "__main__":
    process_excel()
    print(f"处理完成！结果已保存到 {OUTPUT_FILE}")