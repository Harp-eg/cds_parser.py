import pdfplumber
import re
import pandas as pd
import streamlit as st
from io import BytesIO

# 正则表达式模式
patterns = {
    "TOEFL": r"(TOEFL\s*\(?Internet-based\)?|iBT).*?(\d{2,3})\s*to\s*(\d{2,3})",
    "SAT": r"(SAT\s*Evidence-Based\s*Reading\s*and\s*Writing|SAT\s*ERW).*?(\d{3,4})\s*to\s*(\d{3,4})",
    "ACT": r"(ACT\s*Composite).*?(\d{1,2})\s*to\s*(\d{1,2})",
    "GPA": r"(Average\s*GPA|Mean\s*GPA).*?([0-3]\.\d{1,2}|4\.\d{1,2})"
}

def extract_data(pdf_bytes):
    results = {}
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        
        # 提取大学名称
        uni_match = re.search(r"Institution: (.+?)\n", full_text)
        results["University"] = uni_match.group(1) if uni_match else "Unknown"
        
        # 使用正则提取关键数据
        for key, pattern in patterns.items():
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                if key == "GPA":
                    results[key] = match.group(2)
                else:
                    results[key] = f"{match.group(2)}-{match.group(3)}"
            else:
                results[key] = "N/A"
                
        # 提取CDS年份
        year_match = re.search(r"Common Data Set (\d{4})-(\d{4})", full_text)
        results["Year"] = f"{year_match.group(1)}-{year_match.group(2)}" if year_match else "N/A"
        
    except Exception as e:
        st.error(f"解析错误: {str(e)}")
    return results

# Streamlit 界面
st.title("美国本科录取数据提取器")
st.markdown("上传Common Data Set (CDS) PDF文件，自动提取托福/SAT/GPA数据")

uploaded_files = st.file_uploader(
    "上传CDS PDF文件", 
    type="pdf", 
    accept_multiple_files=True
)

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        with st.spinner(f"正在解析 {file.name}..."):
            data = extract_data(file.read())
            data["Filename"] = file.name
            all_data.append(data)
    
    if all_data:
        df = pd.DataFrame(all_data)
        st.success("解析完成！")
        
        # 数据展示
        st.subheader("提取结果")
        st.dataframe(df)
        
        # 下载按钮
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="下载CSV",
            data=csv,
            file_name="university_admissions_data.csv",
            mime="text/csv"
        )

# 使用说明
st.sidebar.markdown("## 使用指南")
st.sidebar.info("""
1. 从大学官网获取Common Data Set (CDS) PDF文件
   - 搜索关键词: "[大学名] Common Data Set"
   - 示例: [Stanford CDS](https://oir.stanford.edu/common-data-set)
2. 上传PDF文件（可多选）
3. 系统自动提取数据并生成表格
4. 下载CSV结果
""")