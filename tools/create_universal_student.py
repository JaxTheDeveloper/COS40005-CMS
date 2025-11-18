from django.contrib.auth import get_user_model
User = get_user_model()
username = 'student_all_access'
email = 'student_all@swin.edu.au'
password = 'password123'
# Create or update the user
user, created = User.objects.update_or_create(
    username=username,
    defaults={
        'email': email,
        'user_type': 'student',
        'is_active': True,
        'is_staff': True,  # allow admin access
        'is_superuser': False,
    }
)
user.set_password(password)
user.save()
print('created' if created else 'updated', user.email, user.user_type, 'is_staff=' + str(user.is_staff))
