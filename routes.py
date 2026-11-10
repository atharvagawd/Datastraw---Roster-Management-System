from flask import Blueprint, request, jsonify
from datetime import date
import calendar
from . import db
from .models import Employee, Brand, Process, Pod, OperatingRule, LeaveRequest, PublicHoliday, RosterEntry, Conflict, GenerationHistory, CompOff
from .scheduler import validate_month, recommend_backup
api=Blueprint('api',__name__)

def payload(): return request.get_json(silent=True) or {}
def err(msg,code=400): return jsonify({'error':msg}),code

@api.get('/health')
def health(): return {'status':'ok','service':'Smart Roster API'}

@api.get('/dashboard')
def dashboard():
    today=date.today(); month=today.month; year=today.year
    entries=RosterEntry.query.filter(db.extract('month',RosterEntry.day)==month,db.extract('year',RosterEntry.day)==year).count()
    total=OperatingRule.query.count()*calendar.monthrange(year,month)[1]
    return {'employees':Employee.query.filter_by(active=True).count(),'brands':Brand.query.filter_by(active=True).count(),'processes':Process.query.count(),'pods':Pod.query.count(),'roster_entries':entries,'coverage_percent':round(min(100,entries/max(1,total)*100),1),'conflicts':Conflict.query.filter_by(resolved=False).count(),'on_leave':LeaveRequest.query.filter_by(status='APPROVED').filter(LeaveRequest.start_date<=today,LeaveRequest.end_date>=today).count(),'upcoming_holidays':[h.json() for h in PublicHoliday.query.filter(PublicHoliday.day>=today).order_by(PublicHoliday.day).limit(5)]}

@api.get('/employees')
def employees(): return jsonify([e.json() for e in Employee.query.order_by(Employee.name).all()])
@api.post('/employees')
def add_employee():
    p=payload(); e=Employee(employee_code=p.get('employee_code'),name=p.get('name'),email=p.get('email'),pod_id=p.get('pod_id'),weekly_off=p.get('weekly_off','Sunday'),preferred_off=p.get('preferred_off'))
    if not e.employee_code or not e.name or not e.email:return err('employee_code, name and email are required')
    try:
        e.brands=Brand.query.filter(Brand.id.in_(p.get('brands',[]))).all(); e.processes=Process.query.filter(Process.id.in_(p.get('processes',[]))).all(); db.session.add(e); db.session.commit(); return e.json(),201
    except Exception as ex: db.session.rollback(); return err(str(ex))
@api.put('/employees/<int:id>')
def update_employee(id):
    e=Employee.query.get_or_404(id); p=payload()
    for k in ['employee_code','name','email','pod_id','active','weekly_off','preferred_off','availability']:
        if k in p:setattr(e,k,p[k])
    if 'brands' in p:e.brands=Brand.query.filter(Brand.id.in_(p['brands'])).all()
    if 'processes' in p:e.processes=Process.query.filter(Process.id.in_(p['processes'])).all()
    try:db.session.commit();return e.json()
    except Exception as ex:db.session.rollback();return err(str(ex))
@api.delete('/employees/<int:id>')
def deactivate_employee(id):
    e=Employee.query.get_or_404(id);e.active=False;db.session.commit();return {'message':'Employee deactivated'}

@api.get('/brands')
def brands():return jsonify([b.json() for b in Brand.query.all()])
@api.post('/brands')
def add_brand():
    p=payload()
    if not p.get('name'):return err('Brand name required')
    b=Brand(name=p['name']);db.session.add(b);db.session.commit();return b.json(),201
@api.put('/brands/<int:id>')
def update_brand(id):
    b=Brand.query.get_or_404(id);p=payload();b.name=p.get('name',b.name);b.active=p.get('active',b.active);db.session.commit();return b.json()
@api.delete('/brands/<int:id>')
def delete_brand(id):b=Brand.query.get_or_404(id);b.active=False;db.session.commit();return {'message':'Brand deactivated'}

@api.get('/processes')
def processes():return jsonify([p.json() for p in Process.query.all()])
@api.post('/processes')
def add_process():
    p=payload();x=Process(name=p.get('name'),code=p.get('code'),description=p.get('description',''))
    if not x.name or not x.code:return err('name and code required')
    db.session.add(x);db.session.commit();return x.json(),201
@api.put('/processes/<int:id>')
def update_process(id):
    x=Process.query.get_or_404(id);p=payload();x.name=p.get('name',x.name);x.code=p.get('code',x.code);x.description=p.get('description',x.description);db.session.commit();return x.json()

@api.get('/pods')
def pods():return jsonify([p.json() for p in Pod.query.all()])
@api.post('/pods')
def add_pod():
    p=payload();x=Pod(name=p.get('name'),lead_name=p.get('lead_name'))
    if not x.name or not x.lead_name:return err('name and lead_name required')
    db.session.add(x);db.session.commit();return x.json(),201

@api.get('/rules')
def rules():return jsonify([r.json() for r in OperatingRule.query.all()])
@api.post('/rules')
def add_rule():
    p=payload();r=OperatingRule(brand_id=p.get('brand_id'),process_id=p.get('process_id'),calendar=p.get('calendar','ALL_DAYS'),min_staff=p.get('min_staff',1),weekdays=p.get('weekdays','0,1,2,3,4,5,6'),shift_start=p.get('shift_start','09:00'),shift_end=p.get('shift_end','18:00'));db.session.add(r);db.session.commit();return r.json(),201
@api.put('/rules/<int:id>')
def update_rule(id):
    r=OperatingRule.query.get_or_404(id);p=payload()
    for k in ['calendar','min_staff','weekdays','shift_start','shift_end']:
        if k in p:setattr(r,k,p[k])
    db.session.commit();return r.json()

@api.get('/leaves')
def leaves():return jsonify([x.json() for x in LeaveRequest.query.order_by(LeaveRequest.start_date).all()])
@api.post('/leaves')
def add_leave():
    p=payload();x=LeaveRequest(employee_id=p['employee_id'],start_date=date.fromisoformat(p['start_date']),end_date=date.fromisoformat(p['end_date']),status=p.get('status','APPROVED'),leave_type=p.get('leave_type','PLANNED'));db.session.add(x);db.session.commit();return x.json(),201
@api.put('/leaves/<int:id>')
def update_leave(id):
    x=LeaveRequest.query.get_or_404(id);p=payload();x.status=p.get('status',x.status);db.session.commit();return x.json()

@api.get('/holidays')
def holidays():return jsonify([h.json() for h in PublicHoliday.query.order_by(PublicHoliday.day).all()])
@api.post('/holidays')
def add_holiday():
    p=payload();h=PublicHoliday(day=date.fromisoformat(p['date']),name=p['name']);db.session.add(h);db.session.commit();return h.json(),201

@api.post('/roster/generate')
def generate():
    p=payload();year=int(p.get('year'));month=int(p.get('month'))
    if month<1 or month>12:return err('Month must be between 1 and 12')
    result=validate_month(year,month);db.session.add(GenerationHistory(month=month,year=year,entries=result['entries'],conflicts=result['conflicts']));db.session.commit();return result
@api.get('/roster')
def roster():
    q=RosterEntry.query
    for param,col in [('year',db.extract('year',RosterEntry.day)),('month',db.extract('month',RosterEntry.day)),('employee_id',RosterEntry.employee_id),('brand_id',RosterEntry.brand_id)]:
        if request.args.get(param):q=q.filter(col==int(request.args[param]))
    if request.args.get('pod_id'):q=q.join(Employee).filter(Employee.pod_id==int(request.args['pod_id']))
    if request.args.get('process_id'):q=q.filter(RosterEntry.process_id==int(request.args['process_id']))
    return jsonify([x.json() for x in q.order_by(RosterEntry.day).all()])
@api.get('/conflicts')
def conflicts():return jsonify([c.json() for c in Conflict.query.filter_by(resolved=False).order_by(Conflict.day).all()])
@api.post('/roster/recommend')
def recommend():
    p=payload();return jsonify(recommend_backup(int(p['brand_id']),int(p['process_id']),p['date'],int(p['exclude_employee_id'])))
@api.post('/roster/manual')
def manual():
    p=payload();d=date.fromisoformat(p['date']);e=Employee.query.get_or_404(int(p['employee_id']));b=Brand.query.get_or_404(int(p['brand_id']));proc=Process.query.get_or_404(int(p['process_id']))
    start=p.get('shift_start','09:00');end=p.get('shift_end','18:00')
    if not e.active or e.availability!='Available':return err('Employee is inactive or unavailable')
    if e.weekly_off==d.strftime('%A'):return err('Employee is on their weekly off')
    if not (b in e.brands and proc in e.processes):return err('Employee is not allocated to this brand and process; update resource allocation first')
    if LeaveRequest.query.filter_by(employee_id=e.id,status='APPROVED').filter(LeaveRequest.start_date<=d,LeaveRequest.end_date>=d).first():return err('Employee has approved leave on this date')
    if CompOff.query.filter_by(employee_id=e.id,day=d,status='APPROVED').first():return err('Employee has approved comp-off on this date')
    overlap=RosterEntry.query.filter_by(day=d,employee_id=e.id).all()
    if any(not (end <= (x.shift_start or '09:00') or start >= (x.shift_end or '18:00')) for x in overlap):return err('Employee already has an overlapping assignment')
    x=RosterEntry(day=d,employee_id=e.id,brand_id=b.id,process_id=proc.id,status='WORKING',shift_start=start,shift_end=end,generated_by='manager');db.session.add(x)
    try:
        db.session.commit()
        result=validate_month(d.year,d.month)
        return {'message':'Assignment saved and roster revalidated','entry':x.json(),'validation':result}
    except Exception as ex:db.session.rollback();return err(f'Assignment rejected: {ex}')
@api.delete('/roster/<int:id>')
def remove_entry(id):x=RosterEntry.query.get_or_404(id);db.session.delete(x);db.session.commit();return {'message':'Assignment removed; regenerate to revalidate coverage'}
@api.post('/roster/revalidate')
def revalidate():
    p=payload();return validate_month(int(p['year']),int(p['month']))
