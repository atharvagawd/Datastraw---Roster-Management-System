from . import db
from datetime import date

employee_brands = db.Table('employee_brands', db.Column('employee_id', db.Integer, db.ForeignKey('employees.id'), primary_key=True), db.Column('brand_id', db.Integer, db.ForeignKey('brands.id'), primary_key=True))
employee_processes = db.Table('employee_processes', db.Column('employee_id', db.Integer, db.ForeignKey('employees.id'), primary_key=True), db.Column('process_id', db.Integer, db.ForeignKey('processes.id'), primary_key=True))

class Employee(db.Model):
    __tablename__='employees'
    id=db.Column(db.Integer, primary_key=True); employee_code=db.Column(db.String(20), unique=True, nullable=False); name=db.Column(db.String(100), nullable=False); email=db.Column(db.String(120), unique=True, nullable=False); pod_id=db.Column(db.Integer, db.ForeignKey('pods.id')); active=db.Column(db.Boolean, default=True); weekly_off=db.Column(db.String(12), default='Sunday'); preferred_off=db.Column(db.String(12)); availability=db.Column(db.String(20), default='Available')
    brands=db.relationship('Brand', secondary=employee_brands, back_populates='employees'); processes=db.relationship('Process', secondary=employee_processes, back_populates='employees')
    def json(self): return {'id':self.id,'employee_code':self.employee_code,'name':self.name,'email':self.email,'pod_id':self.pod_id,'pod':self.pod.name if self.pod else None,'active':self.active,'weekly_off':self.weekly_off,'preferred_off':self.preferred_off,'availability':self.availability,'brands':[b.id for b in self.brands],'brand_names':[b.name for b in self.brands],'processes':[p.id for p in self.processes],'process_names':[p.name for p in self.processes]}

class Pod(db.Model):
    __tablename__='pods'
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(80), unique=True, nullable=False); lead_name=db.Column(db.String(100), nullable=False); employees=db.relationship('Employee', backref='pod')
    def json(self): return {'id':self.id,'name':self.name,'lead_name':self.lead_name,'employee_count':len(self.employees)}

class Process(db.Model):
    __tablename__='processes'
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(80), unique=True, nullable=False); code=db.Column(db.String(12), unique=True, nullable=False); description=db.Column(db.String(250), default='')
    employees=db.relationship('Employee', secondary=employee_processes, back_populates='processes')
    def json(self): return {'id':self.id,'name':self.name,'code':self.code,'description':self.description}

class Brand(db.Model):
    __tablename__='brands'
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(100), unique=True, nullable=False); active=db.Column(db.Boolean, default=True); employees=db.relationship('Employee', secondary=employee_brands, back_populates='brands'); rules=db.relationship('OperatingRule', backref='brand', cascade='all, delete-orphan')
    def json(self): return {'id':self.id,'name':self.name,'active':self.active,'employee_count':len(self.employees),'employees':[e.id for e in self.employees]}

class OperatingRule(db.Model):
    __tablename__='operating_rules'
    id=db.Column(db.Integer, primary_key=True); brand_id=db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False); process_id=db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False); calendar=db.Column(db.String(30), default='ALL_DAYS'); min_staff=db.Column(db.Integer, default=1); weekdays=db.Column(db.String(30), default='0,1,2,3,4,5,6'); shift_start=db.Column(db.String(5), default='09:00'); shift_end=db.Column(db.String(5), default='18:00'); process=db.relationship('Process')
    def json(self): return {'id':self.id,'brand_id':self.brand_id,'brand':self.brand.name,'process_id':self.process_id,'process':self.process.name,'calendar':self.calendar,'min_staff':self.min_staff,'weekdays':self.weekdays,'shift_start':self.shift_start,'shift_end':self.shift_end}

class LeaveRequest(db.Model):
    __tablename__='leave_requests'
    id=db.Column(db.Integer, primary_key=True); employee_id=db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False); start_date=db.Column(db.Date, nullable=False); end_date=db.Column(db.Date, nullable=False); status=db.Column(db.String(20), default='APPROVED'); leave_type=db.Column(db.String(20), default='PLANNED'); employee=db.relationship('Employee')
    def json(self): return {'id':self.id,'employee_id':self.employee_id,'employee':self.employee.name,'start_date':self.start_date.isoformat(),'end_date':self.end_date.isoformat(),'status':self.status,'leave_type':self.leave_type}

class PublicHoliday(db.Model):
    __tablename__='public_holidays'
    id=db.Column(db.Integer, primary_key=True); day=db.Column(db.Date, unique=True, nullable=False); name=db.Column(db.String(100), nullable=False)
    def json(self): return {'id':self.id,'date':self.day.isoformat(),'name':self.name}

class CompOff(db.Model):
    __tablename__='comp_offs'
    id=db.Column(db.Integer, primary_key=True); employee_id=db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False); day=db.Column(db.Date, nullable=False); status=db.Column(db.String(20), default='APPROVED'); employee=db.relationship('Employee')

class RosterEntry(db.Model):
    __tablename__='roster_entries'
    id=db.Column(db.Integer, primary_key=True); day=db.Column(db.Date, nullable=False, index=True); employee_id=db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False); brand_id=db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False); process_id=db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False); status=db.Column(db.String(20), default='WORKING'); shift_start=db.Column(db.String(5)); shift_end=db.Column(db.String(5)); generated_by=db.Column(db.String(40), default='scheduler'); employee=db.relationship('Employee'); brand=db.relationship('Brand'); process=db.relationship('Process')
    __table_args__=(db.UniqueConstraint('day','employee_id','brand_id','process_id',name='uq_roster_assignment'),)
    def json(self): return {'id':self.id,'date':self.day.isoformat(),'employee_id':self.employee_id,'employee':self.employee.name,'brand_id':self.brand_id,'brand':self.brand.name,'process_id':self.process_id,'process':self.process.name,'status':self.status,'shift_start':self.shift_start,'shift_end':self.shift_end}

class Conflict(db.Model):
    __tablename__='conflicts'
    id=db.Column(db.Integer, primary_key=True); day=db.Column(db.Date, nullable=False); severity=db.Column(db.String(20), nullable=False); kind=db.Column(db.String(40), nullable=False); message=db.Column(db.String(300), nullable=False); brand_id=db.Column(db.Integer, db.ForeignKey('brands.id')); process_id=db.Column(db.Integer, db.ForeignKey('processes.id')); employee_id=db.Column(db.Integer, db.ForeignKey('employees.id')); resolved=db.Column(db.Boolean, default=False)
    def json(self): return {'id':self.id,'date':self.day.isoformat(),'severity':self.severity,'kind':self.kind,'message':self.message,'brand_id':self.brand_id,'process_id':self.process_id,'employee_id':self.employee_id,'resolved':self.resolved}

class GenerationHistory(db.Model):
    __tablename__='generation_history'
    id=db.Column(db.Integer, primary_key=True); month=db.Column(db.Integer, nullable=False); year=db.Column(db.Integer, nullable=False); created_at=db.Column(db.DateTime, server_default=db.func.now()); entries=db.Column(db.Integer, default=0); conflicts=db.Column(db.Integer, default=0)
