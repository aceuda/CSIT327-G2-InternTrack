from rest_framework.routers import SimpleRouter
from interntrack_app.views import UserViewSet

router = SimpleRouter()
router.register(r'users', UserViewSet, basename='users')
