from core.planner import Planner

p = Planner()
result = p.plan('I have an interview tomorrow, study Python for 2 hours and go shopping')
print('Tasks found:', len(result['tasks']))
print('Schedule entries:', len(result['schedule']))
print('Error:', result.get('error'))
print()
print('--- Schedule ---')
for e in result['schedule']:
    print(f"  {e.get('start')} - {e.get('end')} : {e.get('title')} [{e.get('type')}]")
