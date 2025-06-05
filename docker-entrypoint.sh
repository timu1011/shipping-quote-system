#!/bin/bash
set -e

# 等待數據庫準備好
echo "等待數據庫準備就緒..."
sleep 5

# 初始化數據庫
echo "初始化數據庫..."
python -c "
from app import app, db
from models import User, Port, ContainerType
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

with app.app_context():
    db.create_all()
    
    # 檢查是否已存在管理員帳號
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # 創建管理員帳號
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(
            username='admin',
            email='admin@example.com',
            password=hashed_password,
            company='管理公司',
            role='admin'
        )
        db.session.add(admin)
        
        # 添加一些基本數據
        # 添加常用港口
        ports = [
            {'code': 'TWKHH', 'name': '高雄', 'country': '台灣', 'region': '亞洲'},
            {'code': 'CNSHA', 'name': '上海', 'country': '中國', 'region': '亞洲'},
            {'code': 'USLAX', 'name': '洛杉磯', 'country': '美國', 'region': '北美'},
            {'code': 'NLRTM', 'name': '鹿特丹', 'country': '荷蘭', 'region': '歐洲'}
        ]
        for port_data in ports:
            port = Port(**port_data)
            db.session.add(port)
        
        # 添加常用櫃型
        container_types = [
            {'code': '20GP', 'name': '20呎標準貨櫃', 'size': '20呎', 'description': '標準乾貨櫃'},
            {'code': '40GP', 'name': '40呎標準貨櫃', 'size': '40呎', 'description': '標準乾貨櫃'},
            {'code': '40HC', 'name': '40呎高櫃', 'size': '40呎', 'description': '高櫃型乾貨櫃'},
            {'code': '45HC', 'name': '45呎高櫃', 'size': '45呎', 'description': '高櫃型乾貨櫃'}
        ]
        for ct_data in container_types:
            ct = ContainerType(**ct_data)
            db.session.add(ct)
        
        db.session.commit()
        print('管理員帳號和基本數據創建成功！')
    else:
        print('管理員帳號已存在，跳過初始化步驟。')
"

# 啟動應用
echo "啟動海運AI自動報價系統..."
gunicorn --bind 0.0.0.0:5000 app:app
