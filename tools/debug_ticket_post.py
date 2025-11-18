from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.utils import timezone
from django.urls import reverse

User = get_user_model()
# create users
staff = User.objects.create_user(username='dbg_staff', email='s@test', password='pw', is_staff=True)
convenor = User.objects.create_user(username='dbg_conv', email='c@test', password='pw', user_type='unit_convenor')
student = User.objects.create_user(username='dbg_stud', email='st@test', password='pw', user_type='student')
client = APIClient()
client.force_authenticate(user=student)
url = reverse('ticket-list')
data = {'title':'API Ticket', 'description':'Need help'}
resp = client.post(url, data, format='json')
print('STATUS', resp.status_code)
print('DATA', getattr(resp, 'data', None))
print('CONTENT', getattr(resp, 'content', None))
