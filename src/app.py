import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from datetime import timedelta

# 創建Flask應用
app = Flask(__name__)

# 基本配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///shipping_quote.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# 初始化擴展
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# 在文件末尾註冊藍圖
def register_blueprints():
    from .auth import auth
    from .quote import quote_bp
    from .admin import admin
    from .main import main_bp

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(quote_bp, url_prefix='/quote')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(main_bp)

# 只有在直接運行此文件時才執行
if __name__ == '__main__':
    register_blueprints()
    app.run(debug=True, host='0.0.0.0')
else:
    # 在WSGI導入時也註冊藍圖
    register_blueprints()
