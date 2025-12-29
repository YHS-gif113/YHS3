import streamlit as st
import bcrypt
from database import get_session, User, create_db_and_tables, get_user_by_account_id, get_user_by_email, add_user
from typing import Optional
import re
from sqlmodel import select
# 初始化数据库
create_db_and_tables()

def hash_password(password: str) -> str:
    """密码哈希加密"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def validate_account_id(account_id: str) -> bool:
    """验证学（工）号格式：学生13位数字，教师8位数字，管理员任意长度"""
    return account_id.isdigit() and (len(account_id) == 13 or len(account_id) == 8)

def validate_password(password: str) -> tuple[bool, str]:
    """验证密码强度：至少8位，包含字母和数字"""
    if len(password) < 8:
        return False, "密码至少需要8位"
    if not any(c.isalpha() for c in password):
        return False, "密码必须包含字母"
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含数字"
    return True, "密码强度符合要求"

def get_role_by_account_id(account_id: str) -> str:
    """根据学（工）号位数判断角色"""
    if len(account_id) == 13:
        return 'student'
    elif len(account_id) == 8:
        return 'teacher'
    else:
        return 'admin'

def register_user(account_id: str, name: str, role: str, department: str, email: str, password: str):
    """注册用户"""
    with get_session() as session:
        # 验证学（工）号格式
        if not validate_account_id(account_id):
            return False, "学（工）号格式错误：学生13位数字，教师8位数字"
        
        # 检查账号是否已存在
        existing_user = session.exec(select(User).where(User.account_id == account_id)).first()
        if existing_user:
            return False, "账号已存在"
        
        # 检查邮箱是否已存在
        existing_email = session.exec(select(User).where(User.email == email)).first()
        if existing_email:
            return False, "邮箱已存在"
        
        # 加密密码
        password_hash = hash_password(password)
        
        # 创建用户
        user = User(
            account_id=account_id, name=name, role=role, department=department, 
            email=email, password_hash=password_hash
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return True, "注册成功"

def login_user(account_id: str, password: str):
    """用户登录"""
    with get_session() as session:
        # 修正：使用正确的查询方式
        user = session.exec(select(User).where(User.account_id == account_id)).first()
        if user and user.is_active and verify_password(password, user.password_hash):
            # 创建用户数据副本，避免 session 关闭后无法访问
            user_data = {
                'user_id': user.user_id,
                'account_id': user.account_id,
                'name': user.name,
                'role': user.role,
                'department': user.department,
                'email': user.email,
                'is_active': user.is_active
            }
            return user_data
        return None

def show_login_page():
    """显示登录页面"""
    st.subheader("用户登录")
    
    account_id = st.text_input("学（工）号")
    password = st.text_input("密码", type="password")
    
    if st.button("登录"):
        user = login_user(account_id, password)
        if user:
            st.session_state['user'] = user
            st.success(f"欢迎, {user['name']}!")
            st.rerun()
        else:
            st.error("账号或密码错误，或账号不存在，请注册或联系管理员")

def show_register_page():
    """显示注册页面"""
    st.title("用户注册")
    
    st.markdown("""  
    **注册说明：**
    - 学生：学号13位数字
    - 教师：工号8位数字
    - 管理员：请联系系统管理员开通账号
    """)
    
    account_id = st.text_input("学（工）号", help="学生13位，教师8位")
    name = st.text_input("姓名")
    
    # 手动选择角色类型
    role_display = st.selectbox(
        "角色类型",
        ["学生", "教师", "管理员"],
        help="请选择您的角色类型"
    )
    role_map = {"学生": "student", "教师": "teacher", "管理员": "admin"}
    role = role_map[role_display]
    
    department = st.text_input("单位/学院")
    email = st.text_input("邮箱")
    password = st.text_input("密码", type="password", help="至少8位，包含字母和数字")
    confirm_password = st.text_input("确认密码", type="password")
    
    if st.button("注册"):
        # 验证密码一致性
        if password != confirm_password:
            st.error("两次密码不一致")
            return
        
        # 验证密码强度
        is_valid, msg = validate_password(password)
        if not is_valid:
            st.error(msg)
            return
        
        # 验证学（工）号格式（仅对学生和教师）
        if role in ['student', 'teacher']:
            if not validate_account_id(account_id):
                st.error("学（工）号格式错误：学生13位数字，教师8位数字")
                return
            
            # 验证角色与学（工）号是否匹配
            expected_role = get_role_by_account_id(account_id)
            if role != expected_role:
                st.error(f"学（工）号与角色不匹配：{account_id}应为{'学生' if expected_role == 'student' else '教师'}")
                return
        
        success, message = register_user(account_id, name, role, department, email, password)
        if success:
            st.success(message)
            st.info("注册成功！请使用学（工）号和密码登录")
            st.rerun()
        else:
            st.error(message)

def show_user_dashboard(user):
    """显示用户仪表盘"""
    st.title(f"欢迎, {user['name']}")
    role_display = "学生" if user['role'] == "student" else "教师" if user['role'] == "teacher" else "管理员"
    st.write(f"角色: {role_display}")
    st.write(f"学（工）号: {user['account_id']}")
    
    # 退出登录按钮
    if st.button("退出登录"):
        del st.session_state['user']
        st.rerun()
    
    st.divider()
    
    # 根据角色显示不同功能
    if user['role'] == 'student':
        show_student_dashboard(user)
    elif user['role'] == 'teacher':
        show_teacher_dashboard(user)
    elif user['role'] == 'admin':
        show_admin_dashboard(user)

def show_student_dashboard(user):
    """学生仪表盘"""
    st.subheader("学生功能")
    st.write("学生功能页面正在开发中...")

def show_teacher_dashboard(user):
    """教师仪表盘"""
    st.subheader("教师功能")
    st.write("教师功能页面正在开发中...")

def show_admin_dashboard(user):
    """管理员仪表盘"""
    st.subheader("管理员功能")
    
    tab1, tab2 = st.tabs(["用户管理", "批量导入"])
    
    with tab1:
        show_user_management()
    
    with tab2:
        from user_import import show_import_page
        show_import_page()

def show_user_management():
    """用户管理界面 - 增删查改"""
    
    # 新增用户表单
    with st.expander("➕ 新增用户", expanded=False):
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_account = st.text_input("学（工）号")
                new_name = st.text_input("姓名")
                new_role = st.selectbox("角色", ["学生", "教师", "管理员"])
            with col2:
                new_dept = st.text_input("单位")
                new_email = st.text_input("邮箱")
                new_pwd = st.text_input("密码", type="password")
            
            if st.form_submit_button("添加用户"):
                role_map = {"学生": "student", "教师": "teacher", "管理员": "admin"}
                success, msg = add_user_by_admin(new_account, new_name, role_map[new_role], new_dept, new_email, new_pwd)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    
    st.divider()
    st.subheader("用户列表")
    
    with get_session() as session:
        users = session.exec(select(User)).all()
        
        if not users:
            st.info("暂无用户")
            return
        
        for u in users:
            role_name = "学生" if u.role == "student" else "教师" if u.role == "teacher" else "管理员"
            status = "✅" if u.is_active else "❌"
            
            with st.expander(f"{status} {u.name} ({u.account_id}) - {role_name}"):
                # 编辑表单
                with st.form(f"edit_{u.user_id}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_account = st.text_input("账号", value=u.account_id, key=f"account_{u.user_id}")
                        edit_name = st.text_input("姓名", value=u.name, key=f"name_{u.user_id}")
                        edit_role = st.selectbox("角色", ["学生", "教师", "管理员"], 
                            index=["学生", "教师", "管理员"].index(role_name), key=f"role_{u.user_id}")
                    with col2:
                        edit_pwd = st.text_input("新密码", type="password", key=f"pwd_{u.user_id}", help="留空则不修改密码")
                        edit_dept = st.text_input("单位", value=u.department or "", key=f"dept_{u.user_id}")
                        edit_email = st.text_input("邮箱", value=u.email, key=f"email_{u.user_id}")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.form_submit_button("保存修改"):
                            role_map = {"学生": "student", "教师": "teacher", "管理员": "admin"}
                            success, msg = update_user_info(u.user_id, edit_account, edit_name, role_map[edit_role], edit_dept, edit_email, edit_pwd)
                            if success:
                                st.success(msg)
                            else:
                                st.error(msg)
                            st.rerun()
                
                # 操作按钮
                col1, col2, col3 = st.columns(3)
                with col1:
                    if u.is_active:
                        if st.button("禁用", key=f"dis_{u.user_id}"):
                            disable_user_by_id(u.user_id)
                            st.rerun()
                    else:
                        if st.button("启用", key=f"en_{u.user_id}"):
                            enable_user_by_id(u.user_id)
                            st.rerun()
                with col2:
                    if st.button("删除", key=f"del_{u.user_id}", type="secondary"):
                        delete_user_by_id(u.user_id)
                        st.rerun()

def add_user_by_admin(account_id, name, role, department, email, password):
    """管理员添加用户"""
    if not account_id or not name or not email or not password:
        return False, "请填写完整信息"
    
    with get_session() as session:
        if session.exec(select(User).where(User.account_id == account_id)).first():
            return False, "账号已存在"
        if session.exec(select(User).where(User.email == email)).first():
            return False, "邮箱已存在"
        
        user = User(
            account_id=account_id, name=name, role=role,
            department=department, email=email,
            password_hash=hash_password(password),
            created_by="admin"
        )
        session.add(user)
        session.commit()
        return True, "用户添加成功"

def update_user_info(user_id, account_id, name, role, department, email, password=None):
    """更新用户信息"""
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            # 检查账号是否与其他用户重复
            if account_id != user.account_id:
                existing = session.exec(select(User).where(User.account_id == account_id)).first()
                if existing:
                    return False, "账号已被其他用户使用"
            
            user.account_id = account_id
            user.name = name
            user.role = role
            user.department = department
            user.email = email
            
            # 如果提供了新密码，则更新密码
            if password and password.strip():
                user.password_hash = hash_password(password)
            
            session.commit()
            return True, "已保存"
        return False, "用户不存在"

def delete_user_by_id(user_id):
    """删除用户"""
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            session.delete(user)
            session.commit()

def disable_user_by_id(user_id: int):
    """禁用用户"""
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            user.is_active = False
            session.commit()

def enable_user_by_id(user_id: int):
    """启用用户"""
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            user.is_active = True
            session.commit()

def main():
    """主应用"""
    if 'user' not in st.session_state:
        st.sidebar.title("导航")
        page = st.sidebar.radio("选择页面", ["登录", "注册"])
        if page == "登录":
            show_login_page()
        elif page == "注册":
            show_register_page()
    else:
        user = st.session_state['user']
        show_user_dashboard(user)

if __name__ == "__main__":
    main()