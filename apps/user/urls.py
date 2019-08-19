from django.contrib.auth.decorators import login_required
from django.urls import path

from apps.user import views
from apps.user.views import RegisterView, LoginView, LogoutView
from apps.user.views import UserInfoView, UserOrderView, UserAddressView

app_name = 'user'

urlpatterns = [
	# path('register/', views.register, name='register'),
	path('register/', RegisterView.as_view(), name='register'),
	path('active/<str:token>/', views.active, name='active'),
	path('login/', LoginView.as_view(), name='login'),
	path('logout/', LogoutView.as_view(), name='logout'),

	path('', UserInfoView.as_view(), name='user'),
	path('order/<int:page>/', UserOrderView.as_view(), name='order'),
	path('address/', UserAddressView.as_view(), name='address'),
]
