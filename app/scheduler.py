import calendar
from datetime import date
from . import db
from .models import Employee, Brand, Process, OperatingRule, LeaveRequest, PublicHoliday, CompOff, RosterEntry, Conflict


def day_operates(rule, day, holidays):
    wd = str(day.weekday()) in rule.weekdays.split(',')
    if not wd: return False
    if rule.calendar == 'WEEKDAYS' and day.weekday() >= 5: return False
    if rule.calendar == 'NO_PUBLIC_HOLIDAYS' and day in holidays: return False
    if rule.calendar == 'SUNDAYS_AND_HOLIDAYS_OFF' and (day.weekday() == 6 or day in holidays): return False
    return True


def validate_month(year, month, persist=True):
    conflicts=[]
    for e in RosterEntry.query.filter(db.extract('year', RosterEntry.day)==year, db.extract('month', RosterEntry.day)==month, RosterEntry.generated_by=='scheduler').all(): db.session.delete(e)
    for c in Conflict.query.filter(db.extract('year', Conflict.day)==year, db.extract('month', Conflict.day)==month).all(): db.session.delete(c)
    holidays={h.day for h in PublicHoliday.query.all()}
    rules=OperatingRule.query.all()
    last=calendar.monthrange(year,month)[1]
    workload={e.id:0 for e in Employee.query.filter_by(active=True).all()}
    for n in range(1,last+1):
        day=date(year,month,n)
        for rule in rules:
            if not day_operates(rule,day,holidays): continue
            assigned=[e for e in Employee.query.filter_by(active=True).all() if rule.brand in e.brands and rule.process in e.processes]
            eligible=[]
            for e in assigned:
                leave=LeaveRequest.query.filter_by(employee_id=e.id,status='APPROVED').filter(LeaveRequest.start_date<=day,LeaveRequest.end_date>=day).first()
                comp=CompOff.query.filter_by(employee_id=e.id,day=day,status='APPROVED').first()
                if leave or comp or e.availability != 'Available' or e.weekly_off == day.strftime('%A'): continue
                already=RosterEntry.query.filter_by(day=day,employee_id=e.id).all()
                overlap=any(not (rule.shift_end <= (x.shift_start or '09:00') or rule.shift_start >= (x.shift_end or '18:00')) for x in already)
                if overlap: continue
                eligible.append(e)
            eligible.sort(key=lambda e:(workload.get(e.id,0), e.preferred_off==day.strftime('%A'), e.id))
            chosen=eligible[:rule.min_staff]
            for e in chosen:
                db.session.add(RosterEntry(day=day,employee_id=e.id,brand_id=rule.brand_id,process_id=rule.process_id,status='WORKING',shift_start=rule.shift_start,shift_end=rule.shift_end))
                workload[e.id]=workload.get(e.id,0)+1
            if len(chosen)<rule.min_staff:
                unavailable=len(assigned)-len(eligible)
                conflicts.append(Conflict(day=day,severity='CRITICAL',kind='COVERAGE_GAP',brand_id=rule.brand_id,process_id=rule.process_id,message=f'{rule.brand.name} / {rule.process.name}: needs {rule.min_staff}, scheduled {len(chosen)}; {unavailable} assigned resource(s) unavailable or off.'))
    db.session.add_all(conflicts)
    db.session.commit()
    return {'entries':RosterEntry.query.filter(db.extract('year',RosterEntry.day)==year,db.extract('month',RosterEntry.day)==month).count(),'conflicts':len(conflicts),'critical':len(conflicts)}


def recommend_backup(brand_id, process_id, day, exclude_employee_id):
    d=date.fromisoformat(day)
    candidates=[]
    for e in Employee.query.filter_by(active=True).all():
        if e.id==exclude_employee_id or not any(b.id==brand_id for b in e.brands) or not any(p.id==process_id for p in e.processes): continue
        if e.weekly_off==d.strftime('%A') or e.availability!='Available': continue
        if LeaveRequest.query.filter_by(employee_id=e.id,status='APPROVED').filter(LeaveRequest.start_date<=d,LeaveRequest.end_date>=d).first(): continue
        if RosterEntry.query.filter_by(day=d,employee_id=e.id).first(): continue
        candidates.append(e)
    return [e.json() for e in candidates]
