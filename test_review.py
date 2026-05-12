import os, requests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autisense.settings')
import django
django.setup()
from apps.users.models import User
from rest_framework_simplejwt.tokens import RefreshToken

psy = User.objects.get(email='psychologist@autisense.com')
token = str(RefreshToken.for_user(psy).access_token)

sess = requests.Session()
sess.headers.update({'Authorization': f'Bearer {token}'})

# Test review endpoint - NO trailing slash
r2 = sess.patch('http://127.0.0.1:8000/assessments/28/review',
    json={'status': 'confirmed', 'note': 'Test confirmation'})
print('Review PATCH =>', r2.status_code, '| status in DB:', r2.json().get('status'))

# Check notification
from apps.notifications.models import Notification
notifs = Notification.objects.filter(recipient_id=11).order_by('-created_at')[:3]
print('Latest notifications for parent 11:')
for n in notifs:
    print(f'  [{n.type}] {n.title}: {n.message[:60]}')

# GET all assessments - check counts
r3 = sess.get('http://127.0.0.1:8000/assessments/')
data = r3.json()
results = data.get('results', data)
pending = [a for a in results if a.get('status') == 'pending']
reviewed = [a for a in results if a.get('status') != 'pending']
print(f'Total: {len(results)}, Pending: {len(pending)}, Reviewed: {len(reviewed)}')
print('Last 5 reviewed IDs and status:', [(a['id'], a['status']) for a in reviewed[-5:]])