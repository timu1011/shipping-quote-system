from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import User, Port, ContainerType, Route, BaseRate, Surcharge, VesselSchedule
from .app import db, bcrypt
from .auth import login_required, admin_required, operator_required
import pandas as pd
from datetime import datetime
import os
import tempfile

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

@admin.route('/import')
@login_required
@admin_required
def import_data():
    return render_template('admin/import_data.html')

@admin.route('/import/rates', methods=['POST'])
@login_required
@admin_required
def import_rates():
    if 'file' not in request.files:
        flash('沒有選擇文件', 'danger')
        return redirect(url_for('admin.import_data'))

    file = request.files['file']
    if file.filename == '':
        flash('沒有選擇文件', 'danger')
        return redirect(url_for('admin.import_data'))

    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('文件格式不正確，請上傳Excel文件', 'danger')
        return redirect(url_for('admin.import_data'))

    # 保存上傳的文件到臨時文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    file.save(temp_file.name)

    try:
        # 讀取Excel文件
        df = pd.read_excel(temp_file.name, engine='openpyxl')

        # 檢查必要的列是否存在
        required_columns = ['起運港代碼', '目的港代碼', '櫃型代碼', '基本運費', '貨幣', '航程時間', '生效日期']
        for col in required_columns:
            if col not in df.columns:
                flash(f'Excel文件缺少必要的列：{col}', 'danger')
                return redirect(url_for('admin.import_data'))

        # 處理每一行數據
        success_count = 0
        error_count = 0

        for index, row in df.iterrows():
            try:
                # 獲取或創建起運港
                origin_port = Port.query.filter_by(code=row['起運港代碼']).first()
                if not origin_port:
                    flash(f'找不到起運港代碼：{row["起運港代碼"]}', 'warning')
                    error_count += 1
                    continue

                # 獲取或創建目的港
                destination_port = Port.query.filter_by(code=row['目的港代碼']).first()
                if not destination_port:
                    flash(f'找不到目的港代碼：{row["目的港代碼"]}', 'warning')
                    error_count += 1
                    continue

                # 獲取或創建櫃型
                container_type = ContainerType.query.filter_by(code=row['櫃型代碼']).first()
                if not container_type:
                    flash(f'找不到櫃型代碼：{row["櫃型代碼"]}', 'warning')
                    error_count += 1
                    continue

                # 獲取或創建航線
                route = Route.query.filter_by(
                    origin_port_id=origin_port.id,
                    destination_port_id=destination_port.id
                ).first()

                if not route:
                    route = Route(
                        origin_port_id=origin_port.id,
                        destination_port_id=destination_port.id,
                        transit_time=int(row['航程時間']),
                        description=f'從{origin_port.name}到{destination_port.name}'
                    )
                    db.session.add(route)
                    db.session.flush()  # 獲取新創建的route.id

                # 處理日期
                effective_date = pd.to_datetime(row['生效日期']).date()
                expiry_date = None
                if '失效日期' in df.columns and not pd.isna(row['失效日期']):
                    expiry_date = pd.to_datetime(row['失效日期']).date()

                # 創建或更新運費
                base_rate = BaseRate.query.filter_by(
                    route_id=route.id,
                    container_type_id=container_type.id,
                    effective_date=effective_date
                ).first()

                if base_rate:
                    base_rate.price = float(row['基本運費'])
                    base_rate.currency = row['貨幣']
                    base_rate.expiry_date = expiry_date
                else:
                    base_rate = BaseRate(
                        route_id=route.id,
                        container_type_id=container_type.id,
                        price=float(row['基本運費']),
                        currency=row['貨幣'],
                        effective_date=effective_date,
                        expiry_date=expiry_date
                    )
                    db.session.add(base_rate)

                success_count += 1

            except Exception as e:
                print(f"Error processing row {index}: {e}")
                error_count += 1

        db.session.commit()
        flash(f'成功導入{success_count}條運費數據，失敗{error_count}條', 'success' if error_count == 0 else 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'導入運費數據時出錯：{str(e)}', 'danger')

    finally:
        # 刪除臨時文件
        os.unlink(temp_file.name)

    return redirect(url_for('admin.import_data'))

@admin.route('/import/schedules', methods=['POST'])
@login_required
@admin_required
def import_schedules():
    if 'file' not in request.files:
        flash('沒有選擇文件', 'danger')
        return redirect(url_for('admin.import_data'))

    file = request.files['file']
    if file.filename == '':
        flash('沒有選擇文件', 'danger')
        return redirect(url_for('admin.import_data'))

    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('文件格式不正確，請上傳Excel文件', 'danger')
        return redirect(url_for('admin.import_data'))

    # 保存上傳的文件到臨時文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    file.save(temp_file.name)

    try:
        # 讀取Excel文件
        df = pd.read_excel(temp_file.name, engine='openpyxl')

        # 檢查必要的列是否存在
        required_columns = ['起運港代碼', '目的港代碼', '船名', '航次', '開航日期', '到達日期']
        for col in required_columns:
            if col not in df.columns:
                flash(f'Excel文件缺少必要的列：{col}', 'danger')
                return redirect(url_for('admin.import_data'))

        # 處理每一行數據
        success_count = 0
        error_count = 0

        for index, row in df.iterrows():
            try:
                # 獲取起運港和目的港
                origin_port = Port.query.filter_by(code=row['起運港代碼']).first()
                if not origin_port:
                    flash(f'找不到起運港代碼：{row["起運港代碼"]}', 'warning')
                    error_count += 1
                    continue

                destination_port = Port.query.filter_by(code=row['目的港代碼']).first()
                if not destination_port:
                    flash(f'找不到目的港代碼：{row["目的港代碼"]}', 'warning')
                    error_count += 1
                    continue

                # 獲取或創建航線
                route = Route.query.filter_by(
                    origin_port_id=origin_port.id,
                    destination_port_id=destination_port.id
                ).first()

                if not route:
                    flash(f'找不到從{row["起運港代碼"]}到{row["目的港代碼"]}的航線', 'warning')
                    error_count += 1
                    continue

                # 處理日期
                departure_date = pd.to_datetime(row['開航日期']).date()
                arrival_date = pd.to_datetime(row['到達日期']).date()

                # 創建或更新船期
                vessel_schedule = VesselSchedule.query.filter_by(
                    route_id=route.id,
                    vessel_name=row['船名'],
                    voyage=row['航次'],
                    departure_date=departure_date
                ).first()

                if vessel_schedule:
                    vessel_schedule.arrival_date = arrival_date
                else:
                    vessel_schedule = VesselSchedule(
                        route_id=route.id,
                        vessel_name=row['船名'],
                        voyage=row['航次'],
                        departure_date=departure_date,
                        arrival_date=arrival_date
                    )
                    db.session.add(vessel_schedule)

                success_count += 1

            except Exception as e:
                print(f"Error processing row {index}: {e}")
                error_count += 1

        db.session.commit()
        flash(f'成功導入{success_count}條船期數據，失敗{error_count}條', 'success' if error_count == 0 else 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'導入船期數據時出錯：{str(e)}', 'danger')

    finally:
        # 刪除臨時文件
        os.unlink(temp_file.name)

    return redirect(url_for('admin.import_data'))

# 添加管理港口的路由
@admin.route('/ports')
@login_required
@admin_required
def manage_ports():
    ports = Port.query.order_by(Port.code).all()
    return render_template('admin/ports.html', ports=ports)

# 添加管理櫃型的路由
@admin.route('/container_types')
@login_required
@admin_required
def manage_container_types():
    container_types = ContainerType.query.order_by(ContainerType.code).all()
    return render_template('admin/container_types.html', container_types=container_types)

# 添加管理運費的路由
@admin.route('/rates')
@login_required
@admin_required
def manage_rates():
    rates = BaseRate.query.order_by(BaseRate.effective_date.desc()).all()
    return render_template('admin/rates.html', rates=rates)

# 添加管理船期的路由
@admin.route('/schedules')
@login_required
@admin_required
def manage_schedules():
    schedules = VesselSchedule.query.order_by(VesselSchedule.departure_date.desc()).all()
    return render_template('admin/schedules.html', schedules=schedules)
