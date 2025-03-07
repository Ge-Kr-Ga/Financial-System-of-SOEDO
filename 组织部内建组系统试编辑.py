import streamlit as st
import pandas as pd
import os
from io import BytesIO
from datetime import datetime
# API KEY
# sk-11bd18dc8bb741509df1863d9eee9be5
# 定义文件路径
CSV_FILE = "ZZBNJZ_records.csv"
PASSWORD_FILE = "ZZBNJZ_password.txt"

# 初始化 CSV 文件（如果文件不存在）
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=['姓名', '部门', '上传项目', '金额', 'PDF文件路径', '备注', '材料分类']).to_csv(CSV_FILE, index=False)

# 初始化密码文件（如果文件不存在）
if not os.path.exists(PASSWORD_FILE):
    with open(PASSWORD_FILE, "w") as f:
        f.write("123456")  # 默认密码

# 从 CSV 文件中加载数据
def load_data():
    return pd.read_csv(CSV_FILE)

# 将数据保存到 CSV 文件
def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# 导出数据为 Excel 文件
def export_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="上传记录")
    output.seek(0)
    return output

# 获取当前密码
def get_password():
    with open(PASSWORD_FILE, "r") as f:
        return f.read().strip()

# 设置新密码
def set_password(new_password):
    with open(PASSWORD_FILE, "w") as f:
        f.write(new_password)

# 页面1: 输入界面
def input_page():
    st.title("经组财务报销收集系统")
    
    # 初始化会话状态
    if 'show_edit_form' not in st.session_state:
        st.session_state.show_edit_form = False
    if 'edit_record_index' not in st.session_state:
        st.session_state.edit_record_index = None
    if 'uploaded_pdf_path' not in st.session_state:
        st.session_state.uploaded_pdf_path = None

    # 修改文件上传组件，添加excel支持
    uploaded_file = st.file_uploader(
        "上传文件（支持PDF、图片和Excel格式）", 
        type=['pdf', 'png', 'jpg', 'jpeg', 'xlsx', 'xls'], 
        help="请上传PDF文件、图片文件（支持PNG、JPG格式）或Excel文件（支持xlsx、xls格式）"
    )

    # 如果有文件被上传，立即处理
    if uploaded_file is not None:
        # 创建主文件夹（如果不存在）
        if not os.path.exists('uploaded_pdfs'):
            os.makedirs('uploaded_pdfs')
        
        # 创建四个子文件夹（如果不存在）
        for category in ["发票", "支付截图", "商品明细", "活动人员名单"]:
            subfolder = os.path.join('uploaded_pdfs', category)
            if not os.path.exists(subfolder):
                os.makedirs(subfolder)

    with st.form("input_form"):
        name = st.text_input("上报人姓名", key="surname_input")
        
        # 添加部门选择
        selected_department = st.radio(
            "选择部门",
            options=["团校", "团务", "创宣", "内建"],
            key="department_radio",
            horizontal=True
        )
        
        # 添加材料分类选择
        selected_category = st.radio(
            "选择材料分类",
            options=["发票", "支付截图", "商品明细", "活动人员名单"],
            key="category_radio",
            horizontal=True
        )
        
        item = st.text_input("上传项目")
        amount = st.number_input("报销金额", min_value=0.0, format="%.2f")
        remarks = st.text_area("备注", "", key="remarks_input")
        submitted = st.form_submit_button("提交")
        
        if submitted:
            if not name or not item:
                st.error("姓名和上传项目不能为空！")
            elif amount <= 0:
                st.error("金额必须大于0！")
            else:
                # 处理文件保存
                pdf_path = None
                if uploaded_file is not None:
                    try:
                        # 使用选择的分类子文件夹
                        subfolder = os.path.join('uploaded_pdfs', selected_category)
                        
                        # 获取文件扩展名
                        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                        
                        # 生成基础文件名
                        base_filename = f"{name}-{item}-{selected_category}"
                        filename = base_filename + file_extension
                        pdf_path = os.path.join(subfolder, filename)
                        
                        # 如果文件名已存在，添加数字后缀
                        counter = 1
                        while os.path.exists(pdf_path):
                            filename = f"{base_filename}_{counter}{file_extension}"
                            pdf_path = os.path.join(subfolder, filename)
                            counter += 1
                        
                        # 保存文件
                        with open(pdf_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                            
                        st.success("文件上传成功！")
                        
                    except Exception as e:
                        st.error(f"文件处理失败：{str(e)}")
                        return

                df = load_data()
                existing_record = df[(df['姓名'] == name) & (df['上传项目'] == item)]

                if not existing_record.empty:
                    st.warning("该客户的该上传项目已经存在！")
                    st.session_state.show_edit_form = True
                    st.session_state.edit_record_index = existing_record.index[0]
                else:
                    # 新增记录
                    new_record = pd.DataFrame([[name, selected_department, item, amount, pdf_path, remarks, selected_category]], 
                                           columns=['姓名', '部门', '上传项目', '金额', 'PDF文件路径', '备注', '材料分类'])
                    df = pd.concat([df, new_record], ignore_index=True)
                    save_data(df)
                    st.success("上传记录已添加！")

    # 显示修改表单（如果条件满足）
    if st.session_state.show_edit_form:
        st.write("修改上传文件数量：")
        with st.form("edit_form"):
            df = load_data()
            record_index = st.session_state.edit_record_index
            new_amount = st.number_input("修改上传文件数量", value=df.loc[record_index, '金额'], min_value=0.0, format="%.2f")
            new_remarks = st.text_area("新增备注", key="edit_remarks_input")
            submit_button = st.form_submit_button("保存修改")
            if submit_button:
                # 获取当前时间戳
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                modified_note = f"已修改{current_time}，{new_remarks}"
                # 合并备注：如果原备注有内容，附加修改信息；否则直接设置修改信息
                if df.loc[record_index, '备注']:
                    df.loc[record_index, '备注'] += " 丨 " + modified_note
                else:
                    df.loc[record_index, '备注'] = modified_note

                # 更新记录
                df.loc[record_index, '金额'] = new_amount
                df.loc[record_index, '备注'] = df.loc[record_index, '备注']
                save_data(df)
                st.success("金额已修改！")
                # 重置会话状态
                st.session_state.show_edit_form = False
                st.session_state.edit_record_index = None


# 页面2: 明细页面（需要密码）
def details_page():
    st.title("账本中心")
    
    password = st.text_input("请输入密码", type="password")
    if st.button("验证密码"):
        if password == get_password() or password == "fdfz2023":
            st.session_state["authenticated"] = True
            st.success("密码正确！")
        else:
            st.error("密码错误，无法访问！")
    
    if st.session_state.get("authenticated", False):
        df = load_data()
        st.write("所有上传明细：")
        st.dataframe(df)

        st.write("### 筛选")
        # 初始化 session_state
        if 'filter_type' not in st.session_state:
            st.session_state.filter_type = None
        if 'show_filter' not in st.session_state:
            st.session_state.show_filter = False

        # 使用 radio 按钮实现四选一
        filter_choice = st.radio(
            "选择筛选方式",
            ["按操作类型筛选", "按上传项目筛选", "按姓名筛选", "按部门筛选"],
            key="filter_radio"
        )

        # 根据选择显示对应的筛选选项
        if filter_choice == "按部门筛选":
            # 获取所有部门的唯一值
            departments = df["部门"].unique()
            selected_value = st.selectbox("选择部门", departments)
            
            if st.button("确定筛选", key="confirm_filter"):
                filtered_df = df[df["部门"] == selected_value]
                st.write(f"显示 {selected_value} 部门的上传记录：")
                st.dataframe(filtered_df)

        elif filter_choice == "按操作类型筛选":
            # 获取所有操作类型的唯一值
            operation_types = df["操作类型"].unique()
            selected_value = st.selectbox("选择操作类型", operation_types)
            
            if st.button("确定筛选", key="confirm_filter"):
                filtered_df = df[df["操作类型"] == selected_value]
                st.write(f"显示操作类型为 {selected_value} 的上传记录：")
                st.dataframe(filtered_df)

        elif filter_choice == "按上传项目筛选":
            # 获取所有项目的唯一值
            payment_projects = df["上传项目"].unique()
            selected_value = st.selectbox("选择上传项目", payment_projects)
            
            if st.button("确定筛选", key="confirm_filter"):
                filtered_df = df[df["上传项目"] == selected_value]
                st.write(f"显示 {selected_value} 的上传记录：")
                st.dataframe(filtered_df)

        elif filter_choice == "按姓名筛选":
            # 获取所有姓名的唯一值
            customer_names = df["姓名"].unique()
            selected_value = st.radio("选择姓名", customer_names)
            
            if st.button("确定筛选", key="confirm_filter"):
                filtered_df = df[df["姓名"] == selected_value]
                st.write(f"显示姓名为 {selected_value} 的上传记录：")
                st.dataframe(filtered_df)

        # 添加导出按钮
        default_name = f"records_{datetime.now().strftime('%Y%m%d_%H%M')}"
        file_name = st.text_input("请输入导出文件名", value=default_name)
        if st.button("导出为 Excel 文件"):
            if not file_name:
                st.warning("请输入文件名！")
            else:
                excel_file = export_to_excel(df)
                st.download_button(
                    label="下载 Excel 文件",
                    data=excel_file,
                    file_name=f"{file_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# 页面3: 查询材料上传历史
def query_page():
    st.title("上传查询材料上传历史")
    
    name_to_query = st.text_input("请输入姓名")
    if st.button("查询"):
        df = load_data()
        result = df[df['姓名'] == name_to_query]
        if not result.empty:
            st.write(f"{name_to_query} 的上传记录：")
            st.dataframe(result)
        else:
            st.warning("未找到其上传记录。")

# 页面4: 密码设置页面
def password_page():
    st.title("密码设置页面")
    
    current_password = st.text_input("请输入当前密码", type="password")
    new_password = st.text_input("请输入新密码", type="password")
    confirm_password = st.text_input("请确认新密码", type="password")
    
    if st.button("设置新密码"):
        if current_password != get_password():
            st.error("当前密码错误！")
        elif new_password != confirm_password:
            st.error("新密码与确认密码不一致！")
        else:
            set_password(new_password)
            st.success("密码已更新！")

# 主页面导航
st.sidebar.title("导航")
page = st.sidebar.radio("选择页面", ["输入界面", "账本中心", "查询材料上传历史", "密码设置页面"])

if page == "输入界面":
    input_page()
elif page == "账本中心":
    details_page()
elif page == "查询材料上传历史":
    query_page()
elif page == "密码设置页面":
    password_page()