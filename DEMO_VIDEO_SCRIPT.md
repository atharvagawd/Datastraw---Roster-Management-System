# 3–5 Minute Demo Video Script

## 0:00–0:25 – Introduction
“Hi, this is my Smart Roster Management System for DataStraw. It helps an operations manager allocate employees across brands and processes, generate monthly schedules and identify coverage gaps before finalising a roster.”

## 0:25–1:00 – Dashboard and sample data
“Here is the operations dashboard. The sample contains 30 fictional employees, 15 brands, five processes and four pods. Twelve brands use a single dedicated resource, while three demonstrate shared-resource operations. The dashboard summarises the workforce, operating rules, coverage and conflicts.”

## 1:00–1:45 – Resource model and operating rules
“Employees are linked to brands and processes through many-to-many relationships. Each brand/process pair has its own operating calendar, minimum staffing and shift window. Employee weekly offs and leave are stored separately, so a client can operate on Sunday while an individual employee is off.”

## 1:45–2:35 – Generate and inspect roster
“I select November 2026 and generate the roster. The scheduler checks each operating day, excludes employees who are unavailable, on approved leave, on comp-off or on weekly off, and avoids overlapping shifts. It then assigns eligible resources while balancing monthly workload. The monthly roster can be filtered by pod, brand and process.”

## 2:35–3:35 – Change management and conflict detection
“To demonstrate a real operational change, I mark a single-resource employee unavailable for one working day and revalidate. The system reports a critical coverage gap for the affected brand/process rather than silently treating the roster as complete. I can inspect backup candidates through the recommendation API, update the employee’s resource allocation, add the backup assignment and revalidate.”

## 3:35–4:20 – Shared-resource scenario
“For a multi-resource brand, the scheduler evaluates the remaining allocated employees after one person becomes unavailable. If enough eligible resources remain to satisfy minimum staffing, coverage can still be met; otherwise the system records a critical gap.”

## 4:20–4:45 – Close
“The solution focuses on reliable coverage, transparent conflicts and manager control. The README documents the architecture, schema, scheduling logic, setup instructions, limitations and answers to all eight assessment questions.”
