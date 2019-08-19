from django.urls import path

from apps.goods import views
from apps.goods.views import IndexView, UploadView, DetailView, ListView

app_name = 'goods'

urlpatterns = [
	path('', IndexView.as_view(), name='index'),
	path('upload/', UploadView.as_view(), name='upload'),
	path('goods/<int:goods_id>', DetailView.as_view(), name='detail'),
	path('goods/list/<int:type_id>/<int:page>/', ListView.as_view(), name='list'),
]