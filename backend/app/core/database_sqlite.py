"""
SQLite数据库配置（用于本地测试）
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 获取数据库URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_geo_monitor.db")

# 创建SQLite引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite特有配置
    echo=True  # 开发环境显示SQL语句
)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    # 导入所有模型以确保它们被注册
    from app.models.simple_user_models import (
        User, Tenant, UserTenant, UserSession, 
        Role, Permission
    )
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 初始化默认权限和角色
    from app.services.permission_service_sqlite import PermissionService
    db = SessionLocal()
    try:
        permission_service = PermissionService(db)
        permission_service.initialize_default_permissions()
        print("数据库初始化完成，默认权限和角色已创建")
    except Exception as e:
        print(f"初始化权限时出错: {e}")
    finally:
        db.close()

def close_db():
    """关闭数据库连接"""
    pass  # SQLite不需要特殊的关闭操作
