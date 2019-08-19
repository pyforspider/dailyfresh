from django.http import JsonResponse
from django.shortcuts import render

from django.views.generic.base import View
from django_redis import get_redis_connection

from apps.goods.models import GoodsSKU
from utils.mixin import LoginRequiredMixin


def index(request):
	pass


# cart/add
class CartAddView(View):

	def post(self, request):
		"""购物车记录添加"""
		# 检验用户是否登录
		user = request.user
		if not user.is_authenticated:
			return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

		# 获取数据
		count = request.POST.get('count')
		sku_id = request.POST.get('sku_id')
		print(sku_id, count, '---------')
		# 数据校验： 完整性，合法性，是否存在
		if not all([count, sku_id]):
			return JsonResponse({'res': 1, 'errmsg': '商品数目出错'})
		try:
			count = int(count)
		except Exception as e:
			return JsonResponse({'res': 2, 'errmsg': '数据不合法'})
		try:
			sku = GoodsSKU.objects.get(id=sku_id)
		except GoodsSKU.DoesNotExist:
			return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

		# 更新redis数据，进行业务处理
		conn = get_redis_connection('default')
		key = 'cart_%s' % user.id
		# 先获取sku_id 的值，不存在返回None
		cart_count = conn.hget(key, sku_id)
		if cart_count:
			count += int(cart_count)

		# 检验商品库存
		if count > sku.stock:
			return JsonResponse({'res': 4, 'errmsg': '超出商品数量'})

		# 设置hash中sku_id的值
		# hest->如果sku_id已经存在，更新数据；sku_id不存在，添加数据
		conn.hset(key, sku_id, count)

		# 计算用户购物车商品的条目数
		total_count = conn.hlen(key)

		# 返回应答
		return JsonResponse({'res': 5, 'message': '添加成功', 'total_count': total_count})


# cart/
class CartInfoView(LoginRequiredMixin, View):

	def get(self, request):
		# 获取用户id
		user = request.user
		key = 'cart_%s' % user.id
		# 获取redis 购物车商品信息
		conn = get_redis_connection('default')
		# {'sku_id1': 商品数目，'sku_id2': 商品数目}
		cart_dict = conn.hgetall(key)
		# print(cart_dict)
		# 遍历获取商品的信息
		skus = []
		total_cost = 0
		total_count = 0
		for sku_id, count in cart_dict.items():
			# 根据商品id获取商品信息
			sku = GoodsSKU.objects.get(id=sku_id)
			# 计算商品的小计
			cost = sku.price*int(count)
			# 把小计, 件数绑定到sku
			sku.cost = cost
			sku.count = int(count)
			skus.append(sku)
			# 计算总价
			total_cost += cost
			# 计算总件数
			total_count += int(count)

		context = {'skus': skus, 'total_cost': total_cost, 'total_count': total_count}
		return render(request, 'cart.html', context=context)


# cart/update
# 更新购物车记录
# 采用ajax post请求
# 前端需要传递的参数：商品id(sku_id) 更新的商品数量(count)
class CartUpdateView(View):

	def post(self, request):
		"""购物车记录添加"""
		# 检验用户是否登录
		user = request.user
		if not user.is_authenticated:
			return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

		# 获取数据
		count = request.POST.get('count')
		sku_id = request.POST.get('sku_id')
		# print(sku_id, count, '---------')
		# 数据校验： 完整性，合法性，是否存在
		if not all([count, sku_id]):
			return JsonResponse({'res': 1, 'errmsg': '商品数目出错'})
		try:
			count = int(count)
		except Exception as e:
			return JsonResponse({'res': 2, 'errmsg': '数据不合法'})
		try:
			sku = GoodsSKU.objects.get(id=sku_id)
		except GoodsSKU.DoesNotExist:
			return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

		# 连接 redis，进行业务处理
		conn = get_redis_connection('default')
		key = 'cart_%s' % user.id

		# 检验商品库存, 再进行 redis 数据库更新
		if count > sku.stock:
			return JsonResponse({'res': 4, 'errmsg': '超出商品数量'})
		conn.hset(key, sku_id, count)

		# 计算用户购物车中商品的总件数{'1': 5, '2': 3}
		total_count = 0
		vals = conn.hvals(key)
		for val in vals:
			total_count += int(val)

		# 返回应答
		return JsonResponse({'res': 5, 'message': '添加成功', 'total_count': total_count})


# 删除购物车记录
# 采用ajax post请求
# 前端需要传递的参数:商品的id(sku_id)
# /cart/delete
class CartDeleteView(View):
	'''购物车记录删除'''

	def post(self, request):
		'''购物车记录删除'''
		user = request.user
		if not user.is_authenticated:
			# 用户未登录
			return JsonResponse({'res': 0, 'errmsg': '请先登录'})

		# 接收参数
		sku_id = request.POST.get('sku_id')

		# 数据的校验
		if not sku_id:
			return JsonResponse({'res': 1, 'errmsg': '无效的商品id'})

		# 校验商品是否存在
		try:
			sku = GoodsSKU.objects.get(id=sku_id)
		except GoodsSKU.DoesNotExist:
			# 商品不存在
			return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

		# 业务处理:删除购物车记录
		conn = get_redis_connection('default')
		cart_key = 'cart_%d' % user.id

		# 删除 hdel
		conn.hdel(cart_key, sku_id)

		# 计算用户购物车中商品的总件数 {'1':5, '2':3}
		total_count = 0
		vals = conn.hvals(cart_key)
		for val in vals:
			total_count += int(val)

		# 返回应答
		return JsonResponse({'res': 3, 'total_count': total_count, 'message':'删除成功'})
