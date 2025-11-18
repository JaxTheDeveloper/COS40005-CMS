from django.contrib.auth import get_user_model
User = get_user_model()
try:
    user = User.objects.get(username='student_all_access')
except User.DoesNotExist:
    user = User.objects.create_user(username='student_all_access', email='student_all@example.com')
user.is_staff = True
user.is_superuser = True
user.set_password('password123')
user.save()
print('promoted', user.username, 'is_staff=', user.is_staff, 'is_superuser=', user.is_superuser)
