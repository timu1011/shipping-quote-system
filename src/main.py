from flask import Blueprint, render_template, redirect, url_for
from .auth import login_required
from .models import Port, ContainerType, Route, BaseRate, VesselSchedule

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('main/index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # 獲取基本統計數據
    port_count = Port.query.count()
    container_type_count = ContainerType.query.count()
    route_count = Route.query.count()
    rate_count = BaseRate.query.count()
    schedule_count = VesselSchedule.query.count()
    
    # 獲取最新的運費數據
    latest_rates = BaseRate.query.order_by(BaseRate.effective_date.desc()).limit(5).all()
    
    # 獲取最新的船期數據
    latest_schedules = VesselSchedule.query.order_by(VesselSchedule.departure_date.desc()).limit(5).all()
    
    return render_template('main/dashboard.html', 
                          port_count=port_count,
                          container_type_count=container_type_count,
                          route_count=route_count,
                          rate_count=rate_count,
                          schedule_count=schedule_count,
                          latest_rates=latest_rates,
                          latest_schedules=latest_schedules)

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    return render_template('main/contact.html')
