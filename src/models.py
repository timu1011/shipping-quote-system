from .app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), default='customer')  # admin, operator, customer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Port(db.Model):
    __tablename__ = 'ports'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Port {self.code} - {self.name}>'

class ContainerType(db.Model):
    __tablename__ = 'container_types'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<ContainerType {self.code} - {self.name}>'

class Route(db.Model):
    __tablename__ = 'routes'

    id = db.Column(db.Integer, primary_key=True)
    origin_port_id = db.Column(db.Integer, db.ForeignKey('ports.id'), nullable=False)
    destination_port_id = db.Column(db.Integer, db.ForeignKey('ports.id'), nullable=False)
    transit_time = db.Column(db.Integer, nullable=False)  # 天數
    description = db.Column(db.String(200), nullable=True)

    origin_port = db.relationship('Port', foreign_keys=[origin_port_id])
    destination_port = db.relationship('Port', foreign_keys=[destination_port_id])

    def __repr__(self):
        return f'<Route {self.id} - {self.origin_port.code} to {self.destination_port.code}>'

class BaseRate(db.Model):
    __tablename__ = 'base_rates'

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    container_type_id = db.Column(db.Integer, db.ForeignKey('container_types.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    effective_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)

    route = db.relationship('Route')
    container_type = db.relationship('ContainerType')

    def __repr__(self):
        return f'<BaseRate {self.id} - {self.route.origin_port.code} to {self.route.destination_port.code} - {self.container_type.code}>'

class Surcharge(db.Model):
    __tablename__ = 'surcharges'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Surcharge {self.code} - {self.name}>'

class RateSurcharge(db.Model):
    __tablename__ = 'rate_surcharges'

    id = db.Column(db.Integer, primary_key=True)
    rate_id = db.Column(db.Integer, db.ForeignKey('base_rates.id'), nullable=False)
    surcharge_id = db.Column(db.Integer, db.ForeignKey('surcharges.id'), nullable=False)
    amount = db.Column(db.Float, nullable=True)  # 如果為空，則使用百分比
    percentage = db.Column(db.Float, nullable=True)  # 如果為空，則使用固定金額
    currency = db.Column(db.String(3), nullable=True)  # 如果為空，則使用基本運費的貨幣

    rate = db.relationship('BaseRate')
    surcharge = db.relationship('Surcharge')

    def __repr__(self):
        return f'<RateSurcharge {self.id} - {self.surcharge.code}>'

class QuoteQuery(db.Model):
    __tablename__ = 'quote_queries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    origin_port_id = db.Column(db.Integer, db.ForeignKey('ports.id'), nullable=False)
    destination_port_id = db.Column(db.Integer, db.ForeignKey('ports.id'), nullable=False)
    container_type_id = db.Column(db.Integer, db.ForeignKey('container_types.id'), nullable=False)
    query_date = db.Column(db.DateTime, default=datetime.utcnow)
    result_rate = db.Column(db.Float, nullable=True)
    result_currency = db.Column(db.String(3), nullable=True)

    user = db.relationship('User')
    origin_port = db.relationship('Port', foreign_keys=[origin_port_id])
    destination_port = db.relationship('Port', foreign_keys=[destination_port_id])
    container_type = db.relationship('ContainerType')

    def __repr__(self):
        return f'<QuoteQuery {self.id} - {self.origin_port.code} to {self.destination_port.code}>'

# 新增的Booking模型
class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    origin_port = db.Column(db.String(100), nullable=False)
    destination_port = db.Column(db.String(100), nullable=False)
    container_type = db.Column(db.String(50), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled

    user = db.relationship('User', backref=db.backref('bookings', lazy=True))

    def __repr__(self):
        return f'<Booking {self.id} - {self.origin_port} to {self.destination_port}>'

# 新增的VesselSchedule模型
class VesselSchedule(db.Model):
    __tablename__ = 'vessel_schedules'

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    vessel_name = db.Column(db.String(100), nullable=False)
    voyage = db.Column(db.String(20), nullable=False)
    departure_date = db.Column(db.Date, nullable=False)
    arrival_date = db.Column(db.Date, nullable=False)

    route = db.relationship('Route')

    def __repr__(self):
        return f'<VesselSchedule {self.id} - {self.vessel_name} {self.voyage}>'
