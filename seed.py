from datetime import date, timedelta
from app import create_app, db
from app.models import Employee, Brand, Process, Pod, OperatingRule, PublicHoliday, LeaveRequest, CompOff
app=create_app()
with app.app_context():
    db.drop_all(); db.create_all()
    processes=[Process(name=n,code=c,description=d) for n,c,d in [('Customer Support','CS','Customer queries and support'),('Abandoned Cart Conversions','ACC','Cart recovery operations'),('Retention','RET','Customer retention'),('Non-Delivery Report','NDR','Delivery exception management'),('Returns & Refunds','RR','Returns operations')]]
    db.session.add_all(processes); db.session.flush()
    pods=[Pod(name=f'Pod {x}',lead_name=lead) for x,lead in zip('ABCD',['Aarav Mehta','Diya Shah','Kabir Rao','Anaya Desai'])];db.session.add_all(pods);db.session.flush()
    brands=[Brand(name=n) for n in ['Aster Home','BluePeak','Cedar & Co','Dawn Living','EverPure','Fable Foods','GlowNest','Harbor Wear','Indigo Kitchen','Juniper Kids','Kite Outdoors','Luma Skin','Mosaic Tech','Nova Wellness','Orchid Living']];db.session.add_all(brands);db.session.flush()
    names=['Aarav','Aditi','Advait','Anaya','Arjun','Avni','Dev','Diya','Ishaan','Ira','Kabir','Kiara','Krish','Mira','Neel','Nisha','Om','Pari','Pranav','Rhea','Rohan','Saanvi','Sameer','Sara','Shaurya','Tara','Ved','Vihaan','Yash','Zoya']
    surnames=['Shah','Patel','Mehta','Rao','Desai','Kulkarni','Joshi','Nair','Kapoor','Iyer']
    employees=[]
    for i,n in enumerate(names):
        e=Employee(employee_code=f'DS{i+1:03}',name=f'{n} {surnames[i%len(surnames)]}',email=f'{n.lower()}{i+1}@datastraw.demo',pod_id=pods[i%4].id,weekly_off=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][i%7],preferred_off=['Sunday','Saturday','Monday'][i%3])
        employees.append(e)
    db.session.add_all(employees);db.session.flush()
        # Assign brands and processes
    for i in range(12):
        e = employees[i]
        b = brands[i]
        e.brands.append(b)

        for p in processes:
            e.processes.append(p)

    for bi, b in enumerate(brands[12:]):
        pool = employees[12 + bi*6 : 18 + bi*6]

        for j, e in enumerate(pool):
            e.brands.append(b)

            primary_process = processes[j % 4]
            e.processes.append(primary_process)

            if j in (0, 3) and processes[0] not in e.processes:
                e.processes.append(processes[0])

            if j == 5:
                e.processes.append(processes[4])

    db.session.flush()
    for b in brands:
        assigned=[e for e in employees if b in e.brands]
        for p in processes:
            eligible=[e for e in assigned if p in e.processes]
            if eligible:
                db.session.add(OperatingRule(brand_id=b.id,process_id=p.id,calendar='SUNDAYS_AND_HOLIDAYS_OFF' if b.id%3==0 else ('NO_PUBLIC_HOLIDAYS' if b.id%3==1 else 'ALL_DAYS'),min_staff=2 if b.id>=13 and p==processes[0] else 1,weekdays='0,1,2,3,4,5,6',shift_start=['09:00','11:00','13:00','15:00','17:00'][processes.index(p)],shift_end=['11:00','13:00','15:00','17:00','19:00'][processes.index(p)]))
    holidays=[(date(2026,11,8),'Regional Holiday'),(date(2026,11,14),'Children’s Day'),(date(2026,11,24),'Operations Holiday')]
    for d,n in holidays:db.session.add(PublicHoliday(day=d,name=n))
    db.session.add(LeaveRequest(employee_id=employees[2].id,start_date=date(2026,11,12),end_date=date(2026,11,14),status='APPROVED',leave_type='PLANNED'))
    db.session.add(LeaveRequest(employee_id=employees[19].id,start_date=date(2026,11,20),end_date=date(2026,11,21),status='PENDING',leave_type='PLANNED'))
    db.session.add(CompOff(employee_id=employees[6].id,day=date(2026,11,18),status='APPROVED'))
    db.session.commit()
    print(f'Seeded {len(employees)} employees, {len(brands)} brands, {len(processes)} processes, {len(pods)} pods, {OperatingRule.query.count()} operating rules')
