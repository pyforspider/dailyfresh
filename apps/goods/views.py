from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View

from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU, Goods
from apps.order.models import OrderGoods


class IndexView(View):

	def get(self, request):

		# 尝试从缓存中获取数据
		context = cache.get('index_page_data')

		# 如果缓存为空
		if context is None:
			# 获取首页商品类型信息
			goods_types = GoodsType.objects.all()
			# 获取首页商品轮播信息
			goods_banners = IndexGoodsBanner.objects.all().order_by('index')
			# 获取首页活动轮播信息
			promotion_banner = IndexPromotionBanner.objects.all().order_by('index')
			# 获取首页分类商品展示信息
			# type_goods_banner = IndexTypeGoodsBanner.objects.all()
			for type in goods_types:
				# 获取type种类首页分类商品的图片展示信息：
				image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
				# 获取type种类首页分类商品的文字展示信息：
				title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
				# 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
				type.type_image = image_banners
				type.type_title = title_banners

			context = {
				'goods_types': goods_types,
				'goods_banners': goods_banners,
				'promotion_banner': promotion_banner,
				'cart_count': 0,
			}

			# 设置缓存
			cache.set('index_page_data', context, 3600)

		# 获取用户购物车中商品的数目
		cart_count = 0
		user = request.user
		from django_redis import get_redis_connection
		if user.is_authenticated:
			con = get_redis_connection('default')
			cart_key = 'cart_%s' % user.id
			cart_count = con.hlen(cart_key)

		context.update(cart_count=cart_count)

		return render(request, 'index.html', context=context)


class UploadView(View):

	def get(self, request):
		return render(request, 'upload_test.html')

	def post(self, request):
		from django.conf import settings
		import os
		image = request.FILES.get('image')
		img_path = os.path.join(settings.BASE_DIR, 'static/upload/image.jpg')

		with open(img_path, 'wb') as fb:
			for part in image.chunks():
				fb.write(part)
				fb.flush()
		return HttpResponse('上传成功')


# /goods/<int:goods_id>
class DetailView(View):

	def get(self, request, goods_id):

		# 获取商品SKU id
		try:
			goods_sku = GoodsSKU.objects.get(id=goods_id)
		except GoodsSKU.DoesNotExist:
			return HttpResponse('商品不存在')
		# 获取商品种类种类信息
		types = GoodsType.objects.all()
		# 获取同类型的其他商品, 新品推荐
		goods_skus = GoodsSKU.objects.filter(type=goods_sku.type).exclude(id=goods_id).order_by('-create_time')
		# 获取相同SPU的其他商品
		same_spu_skus = GoodsSKU.objects.filter(goods=goods_sku.goods).exclude(id=goods_id)
		# 获取商品sku的评论
		sku_orders = OrderGoods.objects.filter(sku=goods_sku).exclude(comment='')
		# 获取用户购物车商品数
		cart_count = 0
		user = request.user
		from django_redis import get_redis_connection
		if user.is_authenticated:
			# 用户已登录
			con = get_redis_connection('default')
			cart_key = 'cart_%s' % user.id
			cart_count = con.hlen(cart_key)

			# 添加用户浏览记录
			conn = get_redis_connection('default')
			history_key = 'history_%s' % user.id
			# 移除列表中的goods_id
			conn.lrem(history_key, 0, goods_id)
			# 在列表左侧插入goods_id
			conn.lpush(history_key, goods_id)
			# 只保存用户最新浏览的五条记录
			conn.ltrim(history_key, 0, 4)

		context = {
			'goods_sku': goods_sku,
			'types': types,
			'goods_skus': goods_skus,         # 相同类型的其他商品，如同属于水果类, 商品推荐
			'cart_count': cart_count,
			'same_spu_skus': same_spu_skus,   # 同一个商品spu， 不同的规格 sku
			'sku_orders': sku_orders,
		}

		return render(request, 'detail.html', context=context)


# goods/list/<int:type_id>/<int:page>/
class ListView(View):

	def get(self, request, type_id, page):
		# 获取所有商品类型
		types = GoodsType.objects.all()
		# 获取特定商品类型
		try:
			goods_type = GoodsType.objects.get(id=type_id)
		except GoodsType.DoesNotExist:
			return HttpResponse('所查找的商品类型不存在')
		# 获取排列顺序
		sort = request.GET.get('sort')
		if sort is None:
			sort = 'default'
		# 获取特定类型商品的所有SKU商品
		if sort == 'price':
			goods_skus = GoodsSKU.objects.filter(type=goods_type).order_by('price')
		elif sort == 'sales':
			goods_skus = GoodsSKU.objects.filter(type=goods_type).order_by('-sales')
		else:
			goods_skus = GoodsSKU.objects.filter(type=goods_type).order_by('-id')
		# 分页器
		paginator = Paginator(goods_skus, 1)
		# 判断页数合法性
		page = int(page)
		if page > paginator.num_pages or page < 1:
			page = 1
		page_object = paginator.page(page)

		print(paginator.page_range, '----------')
		print(range(1, paginator.num_pages+1), '---------------')

		# 页码个数控制
		# 1.页码个数小于等于5，显示全部页码
		# 2.如果当前页是前3页，显示前五页
		# 3.如果当前页是后3页，显示后五页
		# 其他情况，显示当前页前两页，当前页，后两页
		num_pages = paginator.num_pages
		if num_pages <= 5:
			page_li = range(1, num_pages+1)
		if page <= 3:
			page_li = range(1, 6)
		elif num_pages - page < 3:
			page_li = range(num_pages-4, num_pages+1)
		else:
			page_li = range(page-2, page+3)

		# 获取同类型的其他商品, 新品推荐
		new_skus = GoodsSKU.objects.filter(type=goods_type).order_by('-create_time')
		# 获取用户购物车商品数
		cart_count = 0
		user = request.user
		from django_redis import get_redis_connection
		if user.is_authenticated:
			# 用户已登录
			con = get_redis_connection('default')
			cart_key = 'cart_%s' % user.id
			cart_count = con.hlen(cart_key)

		context = {
			'types': types,
			'goods_type': goods_type,
			'sort': sort,

			'paginator': paginator,
			'page_object': page_object,          # 当前页码对象, 必传参数    paginator = page_object.paginator
			'page_li': page_li,

			'new_skus': new_skus,
			'cart_count': cart_count,
		}
		return render(request, 'list.html', context=context)
