from django.contrib import admin

# Register your models here.
from django.core.cache import cache

from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsImage
from apps.goods.models import GoodsSKU, Goods


class BaseModelAdmin(admin.ModelAdmin):

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)

		# 后台管理页面发生变化后，则需要更新静态首页
		from celery_tasks.tasks import generate_static_index_html
		generate_static_index_html.delay()

		# 后台管理页面发生变化后，首页的缓存数据也需要进行删除
		cache.delete('index_page_data')

	def delete_model(self, request, obj):
		super().delete_model(request, obj)

		# 后台管理页面发生变化后，则需要更新静态首页
		from celery_tasks.tasks import generate_static_index_html
		generate_static_index_html.delay()

		# 后台管理页面发生变化后，首页的缓存数据也需要进行删除
		cache.delete('index_page_data')


class GoodsTypeAdmin(BaseModelAdmin):
	pass


class GoodsAdmin(BaseModelAdmin):
	pass


class GoodsSKUAdmin(BaseModelAdmin):
	pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
	pass


class IndexPromotionBannerAdmin(BaseModelAdmin):
	pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
	pass


admin.site.register(GoodsType)
admin.site.register(Goods)

admin.site.register(GoodsSKU)

admin.site.register(IndexGoodsBanner)
admin.site.register(IndexPromotionBanner, BaseModelAdmin)
admin.site.register(IndexTypeGoodsBanner)
# admin.site.register(GoodsImage)
