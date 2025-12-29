import streamlit as st
from auth_system import show_login_page, show_register_page, show_user_dashboard
from user_import import show_import_page
from database import get_session, User, create_db_and_tables

# 初始化数据库
create_db_and_tables()

def main():
    """主应用"""
    st.title("竞赛证书管理系统")
    
    if 'user' not in st.session_state:
        # 未登录状态 - 导航放在标题下方
        st.subheader("请选择操作")
        # 水平布局的导航按钮
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("登录", use_container_width=True):
                st.session_state["selected_page"] = "登录"
        with col2:
            if st.button("注册", use_container_width=True):
                st.session_state["selected_page"] = "注册"
        with col3:
            if st.button("批量导入", use_container_width=True):
                st.session_state["selected_page"] = "批量导入"
        
        # 默认显示登录页面
        selected_page = st.session_state.get("selected_page", "登录")
        if selected_page == "登录":
            show_login_page()
        elif selected_page == "注册":
            show_register_page()
        elif selected_page == "批量导入":
            show_import_page()
    else:
        # 已登录状态 - 显示用户仪表盘
        user = st.session_state['user']
        show_user_dashboard(user)

if __name__ == "__main__":
    main()