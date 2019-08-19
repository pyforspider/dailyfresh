from django.urls import path

from apps.cart import views
from apps.cart.views import CartAddView, CartInfoView, CartUpdateView, CartDeleteView

app_name = 'cart'

urlpatterns = [
	path('index/', views.index, name='index'),
	path('add/', CartAddView.as_view(), name='add'),
	path('', CartInfoView.as_view(), name='cart'),
	path('update/', CartUpdateView.as_view(), name='update'),
	path('delete/', CartDeleteView.as_view(), name='delete'),
]