# 🧪 AI Test Case Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> 基于大语言模型的自动化测试用例生成工具（AI Test Case Generator），支持文本、文档、网页、图片等多种输入方式，快速生成结构化测试用例。

## ✨ 功能特点

- **📝 多源输入**：支持文本描述、Word文档、网页URL、图片（多模态模型）等多种需求输入方式
- **🎯 智能分析**：自动提取测试点，生成符合行业标准的测试用例
- **📊 可编辑表格**：生成的用例以表格形式展示，支持在线编辑、排序、筛选
- **💾 多种导出**：支持导出为Excel、Word、Markdown格式
- **🤖 多模型兼容**：支持DeepSeek、Qwen、GPT-4V等多种大模型，可本地部署（Ollama）
- **⚡ 实时预览**：生成结果即时显示，方便调整
- **🌐 动态网页抓取**：支持JavaScript渲染的动态页面抓取

## 🛠️ 技术栈

- **前端/后端**：Streamlit
- **大模型调用**：OpenAI SDK（兼容OpenAI接口的模型）
- **数据处理**：Pandas
- **文档解析**：python-docx
- **网页抓取**：Requests + BeautifulSoup4 + Playwright
- **导出格式**：openpyxl, python-docx

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourname/AItest-case-generator.git
   cd AItest-case-generator