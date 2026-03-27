# app.py
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from config import SUPPORTED_MODELS, CASE_FIELDS, EXPORT_FORMATS
from modules.model_handler import ModelHandler
from modules.file_parser import FileParser
from modules.web_scraper import WebScraper
from modules.case_generator import CaseGenerator
from modules.exporter import Exporter

# 尝试导入动态网页抓取器（可选）
dynamic_scraper_available = False
try:
    from modules.web_scraper_dynamic import DynamicWebScraper
    dynamic_scraper_available = True
except ImportError:
    pass

# 加载 .env 文件
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="AI Test Case Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1E88E5; text-align: center;}
    .sub-header {font-size: 1.2rem; color: #666; text-align: center;}
    .status-box {padding: 10px; border-radius: 5px; margin: 10px 0;}
    .success-box {background-color: #d4edda; border: 1px solid #c3e6cb;}
    .info-box {background-color: #d1ecf1; border: 1px solid #bee5eb;}
    .warning-box {background-color: #fff3cd; border: 1px solid #ffeeba;}
</style>
""", unsafe_allow_html=True)

# 初始化Session State
def init_session_state():
    if 'test_cases' not in st.session_state:
        st.session_state.test_cases = []
    if 'test_points' not in st.session_state:
        st.session_state.test_points = []
    if 'generation_status' not in st.session_state:
        st.session_state.generation_status = None
    if 'current_input_type' not in st.session_state:
        st.session_state.current_input_type = 'text'

init_session_state()


# ==================== 提前定义显示函数 ====================
def display_cases_table(input_type=None):
    """显示和编辑用例表格"""
    st.subheader("📋 测试用例列表")
    if len(st.session_state.test_cases) == 0:
        st.info("暂无测试用例，请先生成")
        return

    # 如果未传入 input_type，则从会话状态获取
    if input_type is None:
        input_type = st.session_state.get('current_input_type', 'unknown')

    df = pd.DataFrame(st.session_state.test_cases)
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "序号": st.column_config.NumberColumn(min_value=1),
            "优先级": st.column_config.SelectboxColumn(
                options=["P0", "P1", "P2", "P3"]
            ),
            "类型": st.column_config.SelectboxColumn(
                options=["功能测试", "界面测试", "性能测试", "安全测试", "兼容性测试"]
            )
        }
    )
    # 使用包含 input_type 的 key，确保唯一性
    if st.button("💾 保存编辑", key=f"save_edit_{input_type}"):
        st.session_state.test_cases = edited_df.to_dict('records')
        st.success("✅ 编辑已保存")

    # 统计信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("用例总数", len(edited_df))
    with col2:
        st.metric("P0优先级", len(edited_df[edited_df['优先级'] == 'P0']))
    with col3:
        st.metric("功能测试", len(edited_df[edited_df['类型'] == '功能测试']))
    with col4:
        st.metric("识别测试点", len(st.session_state.test_points))

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置面板")
    
    # 模型选择
    model_options = [m.name for m in SUPPORTED_MODELS]
    selected_model = st.selectbox(
        "选择大模型",
        options=model_options,
        help="选择用于生成测试用例的大语言模型"
    )
    
    # API Key 配置（仅从 .env 读取）
    current_model = next(m for m in SUPPORTED_MODELS if m.name == selected_model)

    if current_model.api_key_env:
        # 从环境变量读取 API Key
        env_api_key = os.getenv(current_model.api_key_env, "")
        if env_api_key:
            st.info(f"✅ 已从环境变量读取 {current_model.name} 的 API Key")
            st.caption(f"环境变量: {current_model.api_key_env}")
            # 显示部分 key 作为提示
            masked_key = env_api_key[:8] + "..." if len(env_api_key) > 8 else "***"
            st.code(masked_key, language="")
        else:
            st.warning(f"⚠️ .env 文件中未配置 {current_model.api_key_env}")
            st.caption("请编辑 .env 文件添加 API Key")
        api_key = env_api_key
    else:
        # 本地模型（如 Ollama），不需要 API Key
        st.info(f"ℹ️ {current_model.name} 是本地模型，无需配置 API Key")
        api_key = ""

    st.divider()
    
    # 使用统计
    st.subheader("📊 使用统计")
    st.metric("已生成用例数", len(st.session_state.test_cases))
    st.metric("识别测试点数", len(st.session_state.test_points))
    
    st.divider()
    
    # 帮助信息
    with st.expander("💡 使用帮助"):
        st.markdown("""
        1. 选择大模型和输入方式（文本/文档/网页/图片）
        2. 在 .env 文件中配置对应的 API Key（本地模型除外）
        3. 填写或上传需求内容
        4. 点击生成测试用例
        5. 编辑和完善用例
        6. 导出为所需格式
        """)

# 主页面
st.markdown('<h1 class="main-header">🧪 AI Test Case Generator</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">基于大模型自动化生成高质量测试用例</p>', unsafe_allow_html=True)

# 输入方式选择
input_tabs = st.tabs(["📝 文本输入", "📄 文档上传", "🌐 网页抓取", "🖼️ 图片识别"])

# 初始化模块（不依赖 ModelHandler）
file_parser = FileParser()
web_scraper = WebScraper()
exporter = Exporter()

# ==================== 功能一：文本输入 ====================
with input_tabs[0]:
    st.header("文本输入生成用例")
    
    text_input = st.text_area(
        "请输入需求描述",
        placeholder="例如：用户登录功能，需要输入账号和密码，支持记住密码功能...",
        height=200
    )
    
    col1, col2, col3, col4 = st.columns([1, 1, 1,1])
    with col1:
        generate_btn = st.button("🚀 生成测试用例", type="primary", use_container_width=True)
    with col2:
        regenerate_btn = st.button("🔄 重新生成", use_container_width=True)
    with col3:
        export_btn = st.button("📥 导出用例", use_container_width=True)
    with col4:
        clear_btn = st.button("🗑️ 清空", use_container_width=True, key="clear_text")
    if clear_btn:
        st.session_state.test_cases = []
        st.session_state.test_points = []
        st.session_state.current_input_type = 'text'  # 可选，保持当前标签高亮
        st.rerun()

    if generate_btn or regenerate_btn:
        if not text_input.strip():
            st.warning("⚠️ 请输入需求描述")
        elif not api_key:
            st.warning("⚠️ 请先在侧边栏输入API Key")
        else:
            st.session_state.current_input_type = 'text'
            # 第一阶段：分析测试点
            with st.status("📝 正在分析需求...", expanded=True) as status:
                st.write("🔍 解析需求内容...")
                # 初始化 ModelHandler 和 CaseGenerator
                try:
                    model_handler = ModelHandler(selected_model, api_key)
                    case_generator = CaseGenerator(model_handler)
                    test_points = case_generator.analyze_test_points(text_input)
                    st.write(f"✅ 识别到 {len(test_points)} 个测试点")
                    st.session_state.test_points = test_points

                    st.write("🎯 生成测试用例...")
                    test_cases = case_generator.generate_cases(test_points, text_input)
                    st.write(f"✅ 生成 {len(test_cases)} 条测试用例")
                    st.session_state.test_cases = test_cases
                    status.update(label="✅ 生成完成!", state="complete")

                    st.success(f"🎉 成功生成 {len(test_cases)} 条测试用例")
                except Exception as e:
                    status.update(label="❌ 生成失败", state="error")
                    st.error(f"❌ {str(e)}")
                    st.info("""
                    **排查建议：**
                    1. 检查网络连接是否正常
                    2. 确认 API Key 是否正确
                    3. 确认模型名称是否正确
                    4. 如使用 DeepSeek，确认 API 地址是否为：https://api.deepseek.com
                    5. 如果在国内网络，可能需要使用代理
                    """)
    
    # 显示用例表格
    if st.session_state.test_cases and st.session_state.current_input_type == 'text':
        display_cases_table('text')

# ==================== 功能二：文档上传 ====================
with input_tabs[1]:
    st.header("文档上传生成用例")
    
    uploaded_file = st.file_uploader(
        "上传Word文档",
        type=['doc', 'docx'],
        help="支持 .doc 和 .docx 格式"
    )
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        generate_doc_btn = st.button("🚀 生成测试用例", type="primary", key="doc_gen", use_container_width=True)
    with col2:
        regenerate_doc_btn = st.button("🔄 重新生成", key="doc_reg", use_container_width=True)
    with col3:
        export_doc_btn = st.button("📥 导出用例", key="doc_exp", use_container_width=True)
    with col4:
        clear_btn = st.button("🗑️ 清空", use_container_width=True, key="clear_doc")
    if clear_btn:
        st.session_state.test_cases = []
        st.session_state.test_points = []
        st.session_state.current_input_type = 'text'  # 可选，保持当前标签高亮
        st.rerun()
    
    if generate_doc_btn or regenerate_doc_btn:
        if not uploaded_file:
            st.warning("⚠️ 请上传Word文档")
        elif not api_key:
            st.warning("⚠️ 请先在侧边栏输入API Key")
        else:
            st.session_state.current_input_type = 'document'
            with st.status("📄 正在解析文档...", expanded=True) as status:
                st.write("📖 读取文档内容...")
                doc_content = file_parser.parse_word(uploaded_file)
                st.write(f"✅ 文档解析完成，共 {len(doc_content)} 字符")

                st.write("🔍 分析测试点...")
                # 初始化 ModelHandler 和 CaseGenerator
                model_handler = ModelHandler(selected_model, api_key)
                case_generator = CaseGenerator(model_handler)
                test_points = case_generator.analyze_test_points(doc_content)
                st.write(f"✅ 识别到 {len(test_points)} 个测试点")

                st.write("🎯 生成测试用例...")
                test_cases = case_generator.generate_cases(test_points, doc_content)
                st.session_state.test_cases = test_cases
                status.update(label="✅ 生成完成!", state="complete")
    
    if st.session_state.test_cases and st.session_state.current_input_type == 'document':
        display_cases_table()

# ==================== 功能三：网页抓取 ====================
with input_tabs[2]:
    st.header("网页抓取生成用例")

    url_input = st.text_input(
        "输入网页URL",
        placeholder="https://example.com/login"
    )

    # 选择抓取方式
    st.subheader("抓取方式")
    col1, col2 = st.columns([1, 1])

    with col1:
        use_dynamic = st.checkbox(
            "动态渲染（推荐用于JS加载的页面）",
            value=False,
            help="使用浏览器动态渲染，可以抓取JavaScript加载的内容。需要安装 playwright"
        )

    if use_dynamic and not dynamic_scraper_available:
        st.warning("⚠️ 动态渲染功能不可用，请运行：")
        st.code("pip install playwright && playwright install chromium", language="bash")
        use_dynamic = False

    with col2:
        if use_dynamic:
            wait_time = st.slider(
                "等待时间（秒）",
                min_value=1,
                max_value=10,
                value=3,
                help="页面加载完成后等待的时间，确保动态内容完全加载"
            )

    col1, col2 = st.columns([1, 3])
    with col1:
        fetch_btn = st.button("🌐 抓取网页", use_container_width=True)

    if fetch_btn:
        if not url_input.strip():
            st.warning("⚠️ 请输入网页URL")
        else:
            with st.status("🌐 正在抓取网页...", expanded=True) as status:
                try:
                    if use_dynamic:
                        st.write("🔗 启动浏览器...")
                        st.write(f"⏳ 等待页面加载完成（{wait_time}秒）...")
                        # 使用动态抓取
                        with DynamicWebScraper() as dynamic_scraper:  # 使用上下文管理器
                            page_content = dynamic_scraper.fetch_page(url_input, wait_time=wait_time * 1000)
                        st.write(f"✅ 动态抓取成功，获取 {len(page_content)} 字符内容")
                        # dynamic_scraper = DynamicWebScraper()
                        # page_content = dynamic_scraper.fetch_page(url_input, wait_time=wait_time*1000)
                        # dynamic_scraper.close()
                        st.write(f"✅ 动态抓取成功，获取 {len(page_content)} 字符内容")
                    else:
                        st.write("🔗 连接网页...")
                        # 使用静态抓取
                        page_content = web_scraper.fetch_page(url_input)
                        st.write(f"✅ 静态抓取成功，获取 {len(page_content)} 字符内容")

                    st.session_state.page_content = page_content
                    status.update(label="✅ 抓取完成!", state="complete")

                except Exception as e:
                    status.update(label="❌ 抓取失败", state="error")
                    st.error(f"❌ {str(e)}")
                    # 清理动态抓取器
                    if 'dynamic_scraper' in locals():
                        try:
                            dynamic_scraper.close()
                        except:
                            pass

            # 展示抓取的表单元素
            if 'page_content' in st.session_state and st.session_state.page_content:
                st.subheader("📋 识别到的页面元素")
                #form_elements = web_scraper.extract_form_elements(page_content)
                form_elements = web_scraper.extract_form_elements(st.session_state.page_content)
                if form_elements:
                    # 按类型统计
                    type_counts = {}
                    for elem in form_elements:
                        elem_type = elem.get('type', 'unknown')
                        type_counts[elem_type] = type_counts.get(elem_type, 0) + 1

                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric("元素总数", len(form_elements))
                        for elem_type, count in sorted(type_counts.items()):
                            st.metric(f"{elem_type}", count)

                    with col2:
                        st.json(form_elements)

                    # 添加调试选项
                    with st.expander("🔍 查看原始 HTML 源码"):
                        st.code(page_content, language='html')
                else:
                    st.warning("⚠️ 未识别到表单元素，请检查：")
                    st.info("""
                    1. 确认页面是否包含表单元素（input, button, select 等）
                    2. 确认页面是否是动态加载的（需要 JavaScript）
                    3. 查看下方原始 HTML 源码
                    4. 如果页面是动态渲染的，可能需要使用浏览器自动化工具
                    """)

                    # 显示原始 HTML
                    with st.expander("🔍 查看原始 HTML 源码"):
                        st.code(page_content, language='html')
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        generate_web_btn = st.button("🚀 生成测试用例", type="primary", key="web_gen", use_container_width=True)
    with col2:
        regenerate_web_btn = st.button("🔄 重新生成", key="web_reg", use_container_width=True)
    with col3:
        export_web_btn = st.button("📥 导出用例", key="web_exp", use_container_width=True)
    with col4:
        clear_btn = st.button("🗑️ 清空", use_container_width=True, key="clear_web")
    if clear_btn:
        st.session_state.test_cases = []
        st.session_state.test_points = []
        st.session_state.current_input_type = 'text'  # 可选，保持当前标签高亮
        st.rerun()

    if generate_web_btn or regenerate_web_btn:
        if 'page_content' not in st.session_state or not st.session_state.page_content:
            st.warning("⚠️ 请先抓取网页内容")
        elif not api_key:
            st.warning("⚠️ 请先在侧边栏输入API Key")
        else:
            st.session_state.current_input_type = 'web'
            with st.status("🌐 正在生成用例...", expanded=True) as status:
                # 初始化 ModelHandler 和 CaseGenerator
                model_handler = ModelHandler(selected_model, api_key)
                case_generator = CaseGenerator(model_handler)
                test_points = case_generator.analyze_test_points(st.session_state.page_content)
                st.write(f"识别到 {len(test_points)} 个测试点")  # 调试输出
                test_cases = case_generator.generate_cases(test_points, st.session_state.page_content)
                st.write(f"生成 {len(test_cases)} 条测试用例")  # 调试输出
                st.session_state.test_cases = test_cases
                status.update(label="✅ 生成完成!", state="complete")
            # 在生成按钮代码块后，立即显示用例数量
            st.write(f"当前 session_state 中的用例数: {len(st.session_state.test_cases)}")

    if st.session_state.test_cases and st.session_state.current_input_type == 'web':
        display_cases_table()

# ==================== 功能四：图片识别 ====================
with input_tabs[3]:
    st.header("图片识别生成用例")
    
    # 检查当前模型是否支持多模态
    if not current_model.support_multimodal:
        st.warning(f"⚠️ 当前选择的 {selected_model} 不支持图片识别，请选择支持多模态的模型（如 Qwen-Max、GPT-4V）")
    
    uploaded_image = st.file_uploader(
        "上传图片",
        type=['jpg', 'jpeg', 'png'],
        help="支持 .jpg, .jpeg, .png 格式"
    )
    
    if uploaded_image:
        st.image(uploaded_image, caption="上传的图片", use_container_width=True)
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        generate_img_btn = st.button("🚀 生成测试用例", type="primary", key="img_gen", use_container_width=True)
    with col2:
        regenerate_img_btn = st.button("🔄 重新生成", key="img_reg", use_container_width=True)
    with col3:
        export_img_btn = st.button("📥 导出用例", key="img_exp", use_container_width=True)
    with col4:
        clear_btn = st.button("🗑️ 清空", use_container_width=True, key="clear_img")
    if clear_btn:
        st.session_state.test_cases = []
        st.session_state.test_points = []
        st.session_state.current_input_type = 'text'  # 可选，保持当前标签高亮
        st.rerun()

    if generate_img_btn or regenerate_img_btn:
        if not uploaded_image:
            st.warning("⚠️ 请上传图片")
        elif not api_key:
            st.warning("⚠️ 请先在侧边栏输入API Key")
        elif not current_model.support_multimodal:
            st.error("❌ 当前模型不支持图片识别")
        else:
            st.session_state.current_input_type = 'image'
            with st.status("🖼️ 正在识别图片...", expanded=True) as status:
                st.write("🔍 分析图片内容...")
                # 初始化 ModelHandler 和 CaseGenerator
                model_handler = ModelHandler(selected_model, api_key)
                case_generator = CaseGenerator(model_handler)
                image_description = model_handler.analyze_image(uploaded_image)
                st.write(f"✅ 图片描述：{image_description[:100]}...")

                st.write("🎯 生成测试用例...")
                test_cases = case_generator.generate_cases_from_image(image_description)
                st.session_state.test_cases = test_cases
                status.update(label="✅ 生成完成!", state="complete")
    
    if st.session_state.test_cases and st.session_state.current_input_type == 'image':
        display_cases_table()

# ==================== 用例表格显示与编辑 ====================
# ==================== 导出功能 ====================
def handle_export():
    """处理导出请求"""
    if not st.session_state.test_cases:
        st.warning("⚠️ 没有可导出的用例")
        return
    
    export_format = st.selectbox("选择导出格式", EXPORT_FORMATS)
    
    if st.button("确认导出"):
        import pandas as pd
        df = pd.DataFrame(st.session_state.test_cases)
        
        if export_format == "excel":
            file_bytes = exporter.to_excel(df)
            st.download_button(
                label="📥 下载Excel",
                data=file_bytes,
                file_name="test_cases.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        elif export_format == "word":
            file_bytes = exporter.to_word(df)
            st.download_button(
                label="📥 下载Word",
                data=file_bytes,
                file_name="test_cases.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        elif export_format == "markdown":
            markdown_content = exporter.to_markdown(df)
            st.download_button(
                label="📥 下载Markdown",
                data=markdown_content,
                file_name="test_cases.md",
                mime="text/markdown"
            )

# 在底部添加导出区域
st.divider()
with st.expander("📥 导出测试用例"):
    handle_export()

# 页脚
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>AI Test Case Generator v1.0 | 基于Streamlit + 大语言模型</p>
</div>
""", unsafe_allow_html=True)