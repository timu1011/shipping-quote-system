from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file, session
from .models import Port, ContainerType, Route, BaseRate, VesselSchedule, Booking
from .auth import login_required
from .app import db
from datetime import datetime, timedelta
import io
from reportlab.pdfgen import canvas

quote_bp = Blueprint('quote', __name__)

@quote_bp.route('/')
@login_required
def index():
    ports = Port.query.order_by(Port.name).all()
    container_types = ContainerType.query.order_by(ContainerType.name).all()
    return render_template('quote/index.html', ports=ports, container_types=container_types)

@quote_bp.route('/get_rate', methods=['POST'])
@login_required
def get_rate():
    origin_port_id = request.form.get('origin_port')
    destination_port_id = request.form.get('destination_port')
    container_type_id = request.form.get('container_type')
    
    # 查詢航線
    route = Route.query.filter_by(
        origin_port_id=origin_port_id,
        destination_port_id=destination_port_id
    ).first()
    
    if not route:
        return jsonify({
            'success': False,
            'message': '找不到匹配的航線'
        })
    
    # 查詢當前有效的運費
    today = datetime.utcnow().date()
    base_rate = BaseRate.query.filter(
        BaseRate.route_id == route.id,
        BaseRate.container_type_id == container_type_id,
        BaseRate.effective_date <= today,
        (BaseRate.expiry_date >= today) | (BaseRate.expiry_date.is_(None))
    ).order_by(BaseRate.effective_date.desc()).first()
    
    if not base_rate:
        return jsonify({
            'success': False,
            'message': '找不到有效的運費'
        })
    
    # 查詢最近的船期
    next_month = today + timedelta(days=30)
    vessel_schedules = VesselSchedule.query.filter(
        VesselSchedule.route_id == route.id,
        VesselSchedule.departure_date >= today,
        VesselSchedule.departure_date <= next_month
    ).order_by(VesselSchedule.departure_date).limit(3).all()
    
    schedules_data = []
    for schedule in vessel_schedules:
        schedules_data.append({
            'vessel_name': schedule.vessel_name,
            'voyage': schedule.voyage,
            'departure_date': schedule.departure_date.strftime('%Y-%m-%d'),
            'arrival_date': schedule.arrival_date.strftime('%Y-%m-%d')
        })
    
    # 返回報價和船期信息
    return jsonify({
        'success': True,
        'rate': {
            'price': base_rate.price,
            'currency': base_rate.currency,
            'transit_time': route.transit_time,
            'effective_date': base_rate.effective_date.strftime('%Y-%m-%d')
        },
        'schedules': schedules_data
    })

@quote_bp.route('/ai_quote')
@login_required
def ai_quote():
    return render_template('quote/ai_quote.html')

@quote_bp.route('/process_ai_query', methods=['POST'])
@login_required
def process_ai_query():
    query = request.form.get('query', '')
      query_lower = query.lower()

    # 常見縮寫對應的港口代碼或名稱
    abbreviation_map = {
        'shanghai': ['sha', '上海'],
        'sha': ['sha', '上海'],
        'los angeles': ['lax', '洛杉磯'],
        'lax': ['lax', '洛杉磯'],
        'kaohsiung': ['khh', '高雄'],
        'kh': ['khh', '高雄'],
    }

    for abbr, reps in abbreviation_map.items():
        if abbr in query_lower:
            query_lower += ' ' + ' '.join(reps)
    
    # 這裡可以接入實際的AI處理邏輯
    # 目前使用簡單的關鍵詞匹配作為示例
    
    # 提取可能的起運港和目的港
    ports = Port.query.all()
    origin_port = None
    destination_port = None
    +
    for port in ports:
        port_name_lc = port.name.lower()
        port_code_lc = port.code.lower()
        if port_name_lc in query_lower or port_code_lc in query_lower:
            if f"從{port.name}".lower() in query_lower or f"自{port.name}".lower() in query_lower or f"起運港{port.name}".lower() in query_lower:
                origin_port = port
            elif f"到{port.name}".lower() in query_lower or f"至{port.name}".lower() in query_lower or f"目的港{port.name}".lower() in query_lower:
                destination_port = port
    
    # 提取可能的櫃型
    container_types = ContainerType.query.all()
    container_type = None
    +
    for ct in container_types:
        ct_name_lc = ct.name.lower()
        ct_code_lc = ct.code.lower()
        if ct_name_lc in query_lower or ct_code_lc in query_lower:
            container_type = ct
    
    # 如果找到了必要信息，查詢運費
    if origin_port and destination_port and container_type:
        route = Route.query.filter_by(
            origin_port_id=origin_port.id,
            destination_port_id=destination_port.id
        ).first()
        
        if route:
            today = datetime.utcnow().date()
            base_rate = BaseRate.query.filter(
                BaseRate.route_id == route.id,
                BaseRate.container_type_id == container_type.id,
                BaseRate.effective_date <= today,
                (BaseRate.expiry_date >= today) | (BaseRate.expiry_date.is_(None))
            ).order_by(BaseRate.effective_date.desc()).first()
            
            if base_rate:
                # 查詢最近的船期
                next_month = today + timedelta(days=30)
                vessel_schedules = VesselSchedule.query.filter(
                    VesselSchedule.route_id == route.id,
                    VesselSchedule.departure_date >= today,
                    VesselSchedule.departure_date <= next_month
                ).order_by(VesselSchedule.departure_date).limit(3).all()
                
                schedules_html = ""
                for schedule in vessel_schedules:
                    schedules_html += f"<li>船名：{schedule.vessel_name}，航次：{schedule.voyage}，開航日期：{schedule.departure_date.strftime('%Y-%m-%d')}，到達日期：{schedule.arrival_date.strftime('%Y-%m-%d')}</li>"
                
                if schedules_html:
                    schedules_html = f"<p>最近的船期：</p><ul>{schedules_html}</ul>"
                else:
                    schedules_html = "<p>近期沒有可用的船期</p>"
                
                response = f"""
                <div class="ai-response">
                    <p>根據您的詢問，我找到了從 {origin_port.name} 到 {destination_port.name} 的 {container_type.name} 運費報價：</p>
                    <div class="quote-result">
                        <p>基本運費：{base_rate.price} {base_rate.currency}</p>
                        <p>航程時間：{route.transit_time} 天</p>
                        <p>生效日期：{base_rate.effective_date.strftime('%Y-%m-%d')}</p>
                    </div>
                    {schedules_html}
                    <p>如需更詳細的報價或有其他問題，請隨時詢問。</p>
                </div>
                """
                return jsonify({'success': True, 'response': response})

@quote_bp.route('/book', methods=['POST'])
@login_required
def book():
    """Create a booking from provided data"""
    data = request.get_json() or request.form
    origin = data.get('origin')
    destination = data.get('destination')
    container_type = data.get('container_type')
    if not origin or not destination or not container_type:
        return jsonify({'success': False, 'message': '缺少必要信息'}), 400

    booking = Booking(
        user_id=session.get('user_id'),
        origin_port=origin,
        destination_port=destination,
        container_type=container_type
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify({'success': True, 'booking_id': booking.id})

@quote_bp.route('/<int:booking_id>/pdf')
@login_required
def booking_pdf(booking_id):
    """Generate a simple PDF quote for the booking"""
    booking = Booking.query.get_or_404(booking_id)

    # 查找航線及運費資料
    origin_port = Port.query.filter((Port.name == booking.origin_port) | (Port.code == booking.origin_port)).first()
    destination_port = Port.query.filter((Port.name == booking.destination_port) | (Port.code == booking.destination_port)).first()
    base_rate = None
    schedule = None
    if origin_port and destination_port:
        route = Route.query.filter_by(origin_port_id=origin_port.id, destination_port_id=destination_port.id).first()
        if route:
            today = datetime.utcnow().date()
            base_rate = BaseRate.query.filter(
                BaseRate.route_id == route.id,
                BaseRate.effective_date <= today,
                (BaseRate.expiry_date >= today) | (BaseRate.expiry_date.is_(None))
            ).order_by(BaseRate.effective_date.desc()).first()
            schedule = VesselSchedule.query.filter_by(route_id=route.id).order_by(VesselSchedule.departure_date).first()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(50, 800, 'Booking Confirmation')
    p.drawString(50, 780, f'Booking ID: {booking.id}')
    p.drawString(50, 760, f'Origin: {booking.origin_port}')
    p.drawString(50, 740, f'Destination: {booking.destination_port}')
    p.drawString(50, 720, f'Container Type: {booking.container_type}')
    if base_rate:
        p.drawString(50, 700, f'Rate: {base_rate.price} {base_rate.currency}')
    if schedule:
        p.drawString(50, 680, f'Schedule: {schedule.vessel_name} {schedule.voyage} {schedule.departure_date}')
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name=f'quote_{booking.id}.pdf')    
    # 如果無法提取完整信息或找不到匹配的運費
    return jsonify({
        'success': True,
        'response': """
        <div class="ai-response">
            <p>很抱歉，我無法根據您提供的信息找到匹配的運費報價。請提供更完整的信息，包括：</p>
            <ul>
                <li>起運港（例如：高雄、上海）</li>
                <li>目的港（例如：洛杉磯、鹿特丹）</li>
                <li>櫃型（例如：20呎標準貨櫃、40呎高櫃）</li>
            </ul>
            <p>例如：「請提供從高雄到洛杉磯的40呎高櫃運費報價」</p>
        </div>
        """
    })
