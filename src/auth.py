from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .app import db, bcrypt
from .models import User
from datetime import datetime
import functools

# 創建藍圖
auth = Blueprint('auth', __name__)

# 登入檢查裝飾器
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('請先登入', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# 管理員權限檢查裝飾器
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('您沒有權限訪問此頁面', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# 操作員或管理員權限檢查裝飾器
def operator_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] not in ['admin', 'operator']:
            flash('您沒有權限訪問此頁面', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# 登入頁面
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            # 更新最後登入時間
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # 存儲用戶信息到session
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            # 根據角色重定向到不同頁面
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        else:
            flash('用戶名或密碼錯誤', 'danger')
    
    return render_template('auth/login.html')

# 登出
@auth.route('/logout')
def logout():
    session.clear()
    flash('您已成功登出', 'success')
    return redirect(url_for('auth.login'))

# API登入
@auth.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and bcrypt.check_password_hash(user.password, password):
        # 更新最後登入時間
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 創建JWT令牌
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': '用戶名或密碼錯誤'
        }), 401
