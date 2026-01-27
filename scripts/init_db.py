#!/usr/bin/env python3
"""
GEO Monitor Database Initialization Script
"""

import psycopg2
import sys

# Supabase 连接配置 - 请从 Supabase Dashboard 获取密码
# Settings -> Database -> Database password
DB_CONFIG = {
    'host': 'db.mqmzimtckgollewnvlli.supabase.co',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': sys.argv[1] if len(sys.argv) > 1 else None
}

def read_sql_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def main():
    if not DB_CONFIG['password']:
        print("❌ 错误：请提供数据库密码")
        print("用法: python init_db.py <数据库密码>")
        print("")
        print("获取密码步骤：")
        print("1. 登录 https://supabase.com/dashboard/project/mqmzimtckgollewnvlli")
        print("2. Settings -> Database")
        print("3. 复制 'Database password'")
        return
    
    try:
        print("正在连接 Supabase 数据库...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ 连接成功！")
        
        # 读取并执行 SQL
        sql_file = '/Users/ss/Documents/Project/Web/geo-monitor/database/init.sql'
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"正在执行 {sql_file}...")
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        
        print("🎉 数据库初始化完成！")
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ 数据库错误: {e}")

if __name__ == '__main__':
    main()
