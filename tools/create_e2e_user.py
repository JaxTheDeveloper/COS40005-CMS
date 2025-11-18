from django.contrib.auth import get_user_model
User = get_user_model()
user, created = User.objects.get_or_create(username='e2e_user', defaults={'email':'e2e@example.com'})
user.set_password('password123')
user.save()
print('created' if created else 'updated')
