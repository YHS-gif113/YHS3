from sqlmodel import SQLModel, create_engine, Session, select, Field
from typing import Optional, List
from datetime import datetime
import os
from contextlib import contextmanager
# 数据库配置
DATABASE_URL = "sqlite:///./certificates.db"
 
# 创建数据库引擎
engine = create_engine(DATABASE_URL, echo=True)
 
def create_db_and_tables():
    """创建数据库表"""
    SQLModel.metadata.create_all(engine)
 
@contextmanager
def get_session():
    """获取数据库会话"""
    with Session(engine) as session:
        yield session
 
# 用户模型
class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)  # 主键
    account_id: str = Field(index=True, unique=True)  # 唯一索引，用于登录
    name: str
    role: str
    department: Optional[str] = None
    email: str = Field(index=True, unique=True)
    password_hash: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = "self_register"
 
# 证书模型
class Certificate(SQLModel, table=True):
    cert_id: Optional[int] = Field(default=None, primary_key=True)
    submitter_id: int
    submitter_role: str
    student_id: str
    student_name: str
    department: Optional[str] = None
    competition_name: Optional[str] = None
    award_category: Optional[str] = None
    award_level: Optional[str] = None
    competition_type: Optional[str] = None
    organizer: Optional[str] = None
    award_date: Optional[str] = None
    advisor: Optional[str] = None
    file_path: str
    extraction_method: Optional[str] = None
    extraction_confidence: Optional[float] = None
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
 
# 文件模型
class File(SQLModel, table=True):
    file_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    upload_time: datetime = Field(default_factory=datetime.now)
 
# 配置模型
class SystemConfig(SQLModel, table=True):
    config_id: Optional[int] = Field(default=None, primary_key=True)
    config_key: str = Field(index=True, unique=True)
    config_value: Optional[str] = None
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.now)
    updated_by: Optional[int] = None
 
# 用户操作函数
def add_user(session, account_id: str, name: str, role: str, department: str, email: str, password_hash: str, created_by: str = 'self_register'):
    """添加用户"""
    user = User(account_id=account_id, name=name, role=role, department=department, email=email, password_hash=password_hash, created_by=created_by)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
 
def get_user_by_account_id(session, account_id: str):
    """根据账号ID获取用户"""
    return session.get(User, account_id)
 
def get_user_by_email(session, email: str):
    """根据邮箱获取用户"""
    return session.exec(select(User).where(User.email == email)).first()
 
def update_user(session, user_id: int, **kwargs):
    """更新用户信息"""
    user = session.get(User, user_id)
    if user:
        for key, value in kwargs.items():
            setattr(user, key, value)
        session.commit()
        session.refresh(user)
    return user
 
def disable_user(session, user_id: int):
    """禁用用户"""
    user = session.get(User, user_id)
    if user:
        user.is_active = False
        session.commit()
        session.refresh(user)
    return user
 
def enable_user(session, user_id: int):
    """启用用户"""
    user = session.get(User, user_id)
    if user:
        user.is_active = True
        session.commit()
        session.refresh(user)
    return user
 
def get_all_users(session):
    """获取所有用户"""
    return session.exec(select(User)).all()
 
def get_users_by_role(session, role: str):
    """根据角色获取用户"""
    return session.exec(select(User).where(User.role == role)).all()
 
# 证书操作函数
def add_certificate(session, submitter_id: int, submitter_role: str, student_id: str, student_name: str, 
                  department: str, competition_name: str, award_category: str, award_level: str,
                  competition_type: str, organizer: str, award_date: str, advisor: str, 
                  file_path: str, extraction_method: str = None, extraction_confidence: float = None):
    """添加证书信息"""
    cert = Certificate(
        submitter_id=submitter_id, submitter_role=submitter_role, student_id=student_id, 
        student_name=student_name, department=department, competition_name=competition_name,
        award_category=award_category, award_level=award_level, competition_type=competition_type,
        organizer=organizer, award_date=award_date, advisor=advisor, file_path=file_path,
        extraction_method=extraction_method, extraction_confidence=extraction_confidence
    )
    session.add(cert)
    session.commit()
    session.refresh(cert)
    return cert
 
def get_certificates(session, skip: int = 0, limit: int = 10, **filters):
    """获取证书列表"""
    statement = select(Certificate).offset(skip).limit(limit)
    for key, value in filters.items():
        if hasattr(Certificate, key):
            statement = statement.where(getattr(Certificate, key) == value)
    return session.exec(statement).all()
 
def get_certificate_by_id(session, cert_id: int):
    """根据ID获取证书"""
    return session.get(Certificate, cert_id)
 
def update_certificate_status(session, cert_id: int, status: str):
    """更新证书状态"""
    cert = session.get(Certificate, cert_id)
    if cert:
        cert.status = status
        if status == 'submitted':
            cert.submitted_at = datetime.now()
        session.commit()
        session.refresh(cert)
    return cert
 
# 文件操作函数
def add_file(session, user_id: int, file_name: str, file_path: str, file_type: str, file_size: int):
    """添加文件记录"""
    file_record = File(user_id=user_id, file_name=file_name, file_path=file_path, file_type=file_type, file_size=file_size)
    session.add(file_record)
    session.commit()
    session.refresh(file_record)
    return file_record
 
# 配置操作函数
def get_config(session, key: str):
    """获取配置值"""
    config = session.exec(select(SystemConfig).where(SystemConfig.config_key == key)).first()
    return config.config_value if config else None
 
def set_config(session, key: str, value: str, description: str = None, updated_by: int = None):
    """设置配置值"""
    config = session.exec(select(SystemConfig).where(SystemConfig.config_key == key)).first()
    if config:
        config.config_value = value
        config.updated_at = datetime.now()
        config.updated_by = updated_by
    else:
        config = SystemConfig(config_key=key, config_value=value, description=description, updated_by=updated_by)
        session.add(config)
    session.commit()
    session.refresh(config)
    return config