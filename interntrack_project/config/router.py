from rest_framework.routers import SimpleRouter
from interntrack_app.views import UserViewset

router = SimpleRouter()
router.register(r'users', UserViewset, basename='users')
