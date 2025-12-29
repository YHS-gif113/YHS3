import streamlit as st
import pandas as pd
import bcrypt
from database import get_session, User, add_user
from auth_system import hash_password, validate_account_id, get_role_by_account_id
from sqlmodel import select
from datetime import datetime

def generate_default_password(account_id: str) -> str:
    """为批量导入用户生成默认密码"""
    return f"{account_id[-6:]}"

def validate_excel_format(df: pd.DataFrame) -> tuple[bool, str]:
    """验证Excel文件格式"""
    required_columns = ['学（工）号', '姓名', '角色类型', '单位', '邮箱']
    
    # 检查必填列
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"缺少必填列: {', '.join(missing_columns)}"
    
    return True, "格式验证通过"

def import_users_from_excel(file, created_by: str = 'admin') -> dict:
    """从Excel导入用户"""
    result = {
        'success': [],
        'failed': [],
        'duplicate': []
    }
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file)
        
        # 验证格式
        is_valid, message = validate_excel_format(df)
        if not is_valid:
            st.error(message)
            return result
        
        # 逐行处理
        with get_session() as session:
            for index, row in df.iterrows():
                try:
                    account_id = str(row['学（工）号']).strip()
                    name = str(row['姓名']).strip()
                    role_display = str(row['角色类型']).strip()
                    department = str(row['单位']).strip()
                    email = str(row['邮箱']).strip()
                    
                    # 角色映射
                    role_map = {'学生': 'student', '教师': 'teacher', '管理员': 'admin'}
                    role = role_map.get(role_display, role_display.lower())
                    
                    # 验证学（工）号格式
                    if not validate_account_id(account_id):
                        result['failed'].append({
                            'account_id': account_id,
                            'name': name,
                            'reason': '学（工）号格式错误'
                        })
                        continue
                    
                    # 检查是否已存在
                    existing_user = session.exec(
                        select(User).where(User.account_id == account_id)
                    ).first()
                    
                    if existing_user:
                        result['duplicate'].append({
                            'account_id': account_id,
                            'name': name,
                            'reason': '学（工）号已存在'
                        })
                        continue
                    
                    # 检查邮箱是否已存在
                    existing_email = session.exec(
                        select(User).where(User.email == email)
                    ).first()
                    
                    if existing_email:
                        result['failed'].append({
                            'account_id': account_id,
                            'name': name,
                            'reason': '邮箱已存在'
                        })
                        continue
                    
                    # 获取或生成密码
                    if '初始密码' in df.columns and pd.notna(row['初始密码']):
                        password = str(row['初始密码']).strip()
                    else:
                        password = generate_default_password(account_id)
                    
                    # 加密密码
                    password_hash = hash_password(password)
                    
                    # 创建用户
                    user = User(
                        account_id=account_id,
                        name=name,
                        role=role,
                        department=department,
                        email=email,
                        password_hash=password_hash,
                        created_by=created_by
                    )
                    session.add(user)
                    session.commit()
                    
                    result['success'].append({
                        'account_id': account_id,
                        'name': name,
                        'password': password
                    })
                    
                except Exception as e:
                    result['failed'].append({
                        'account_id': account_id if 'account_id' in locals() else '未知',
                        'name': name if 'name' in locals() else '未知',
                        'reason': str(e)
                    })
                    continue
        
    except Exception as e:
        st.error(f"文件处理错误: {str(e)}")
    
    return result

def generate_import_report(result: dict) -> str:
    """生成导入报告"""
    report = "# 用户批量导入报告\n\n"
    report += "本报告记录了最近一次用户批量导入的详细结果，包括成功、失败和重复的记录。\n\n"
    report += "- **成功导入**：成功写入数据库的用户条目。\n"
    report += "- **失败**：因格式错误或邮箱重复等原因未能导入的条目。\n"
    report += "- **重复**：学（工）号已存在，未导入的条目。\n\n"
    report += f"> 导入时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += "---\n\n"
    report += "## 导入结果\n\n"
    report += f"- 成功：{len(result['success'])} 条\n"
    report += f"- 失败：{len(result['failed'])} 条\n"
    report += f"- 重复：{len(result['duplicate'])} 条\n\n"
    
    # 成功记录
    if result['success']:
        report += "### 成功导入的用户\n\n"
        report += "| 学（工）号 | 姓名 | 初始密码 |\n"
        report += "|-----------|------|----------|\n"
        for user in result['success']:
            report += f"| {user['account_id']} | {user['name']} | {user['password']} |\n"
        report += "\n"
    
    # 失败记录
    if result['failed']:
        report += "### 导入失败的记录\n\n"
        report += "| 学（工）号 | 姓名 | 失败原因 |\n"
        report += "|-----------|------|----------|\n"
        for user in result['failed']:
            report += f"| {user['account_id']} | {user['name']} | {user['reason']} |\n"
        report += "\n"
    
    # 重复记录
    if result['duplicate']:
        report += "### 重复的记录（未导入）\n\n"
        report += "| 学（工）号 | 姓名 | 原因 |\n"
        report += "|-----------|------|------|\n"
        for user in result['duplicate']:
            report += f"| {user['account_id']} | {user['name']} | {user['reason']} |\n"
        report += "\n"
    
    return report

def show_import_page():
    """显示用户批量导入页面"""
    st.title("用户批量导入")
    st.write("管理员可通过上传Excel文件批量导入用户信息")
    
    # 显示模板说明
    st.subheader("📋 Excel文件格式要求")
    st.markdown("""
    **必填列：**
    - 学（工）号：学生13位数字，教师8位数字
    - 姓名：用户真实姓名
    - 角色类型：学生/教师/管理员
    - 单位：所属学院或部门
    - 邮箱：用于接收系统通知
    
    **可选列：**
    - 初始密码：未提供则自动生成（使用学工号后6位）
    """)
    
    # 显示模板示例
    with st.expander("查看Excel模板示例"):
        sample_data = pd.DataFrame({
            '学（工）号': ['2021010101001', '12345678', '2021010101002'],
            '姓名': ['张三', '李老师', '王五'],
            '角色类型': ['学生', '教师', '学生'],
            '单位': ['计算机学院', '信息学院', '计算机学院'],
            '邮箱': ['zhangsan@example.com', 'liteacher@example.com', 'wangwu@example.com'],
            '初始密码': ['123456', 'teacher123', '']
        })
        st.dataframe(sample_data, use_container_width=True)
    
    # 文件上传
    st.subheader("📤 上传用户信息文件")
    uploaded_file = st.file_uploader(
        "选择Excel文件",
        type=['xlsx', 'xls'],
        help="请上传包含用户信息的Excel文件"
    )
    
    if uploaded_file is not None:
        st.success(f"文件已上传: {uploaded_file.name}")
        
        # 预览数据
        try:
            df_preview = pd.read_excel(uploaded_file)
            st.subheader("📊 数据预览")
            st.dataframe(df_preview.head(10), use_container_width=True)
            st.info(f"共 {len(df_preview)} 条记录")
            
            # 重置文件指针
            uploaded_file.seek(0)
        except Exception as e:
            st.error(f"文件读取错误: {str(e)}")
            return
        
        # 导入按钮
        if st.button("🚀 开始导入", type="primary"):
            with st.spinner("正在导入用户..."):
                result = import_users_from_excel(uploaded_file, created_by='admin_import')
                
                # 显示结果
                st.subheader("📈 导入结果")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("成功", len(result['success']), delta=None, delta_color="normal")
                with col2:
                    st.metric("失败", len(result['failed']), delta=None, delta_color="inverse")
                with col3:
                    st.metric("重复", len(result['duplicate']), delta=None, delta_color="off")
                
                # 生成并保存报告
                report_content = generate_import_report(result)
                report_path = "d:/python/实训/项目2/import_test_report.md"
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                # 显示详细结果
                if result['success']:
                    with st.expander(f"✅ 成功导入 ({len(result['success'])} 条)", expanded=True):
                        success_df = pd.DataFrame(result['success'])
                        st.dataframe(success_df, use_container_width=True)
                        st.warning("⚠️ 请妥善保管初始密码，建议通知用户首次登录后修改密码")
                
                if result['failed']:
                    with st.expander(f"❌ 导入失败 ({len(result['failed'])} 条)"):
                        failed_df = pd.DataFrame(result['failed'])
                        st.dataframe(failed_df, use_container_width=True)
                
                if result['duplicate']:
                    with st.expander(f"🔄 重复记录 ({len(result['duplicate'])} 条)"):
                        duplicate_df = pd.DataFrame(result['duplicate'])
                        st.dataframe(duplicate_df, use_container_width=True)
                
                st.success(f"✅ 导入报告已保存至: {report_path}")
                
                # 提供报告下载
                st.download_button(
                    label="📥 下载导入报告",
                    data=report_content,
                    file_name=f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
