import re
from time import sleep

from django.contrib.auth import authenticate, login, logout

from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from django.views.generic.base import View

from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods
from apps.user.models import User, Address

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_register_active_email

from django.conf import settings

from utils.mixin import LoginRequiredMixin


# user/register/
class RegisterView(View):

	def get(self, request):
		return render(request, 'register.html')

	def post(self, request):
		user_name = request.POST.get('user_name')
		pwd = request.POST.get('pwd')
		email = request.POST.get('email')
		allow = request.POST.get('allow')

		if not all([user_name, pwd, email]):
			return render(request, 'register.html', {'errmsg': '数据不完整'})      # html 需要挖坑

		if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
			return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

		if allow != 'on':
			return render(request, 'register.html', {'errmsg': '请同意协议'})

		try:
			user = User.objects.get(username=user_name)
			return render(request, 'register.html', {'errmsg': '%s 用户名已被使用' % user})

		except User.DoesNotExist:
			user = User.objects.create_user(user_name, email, pwd)
			user.is_active = 0
			user.save()

			# 加密用户的信息，生成token
			serializer = Serializer(settings.SECRET_KEY, 3600)
			info = {'user_id': user.id}
			token = serializer.dumps(info)
			token = token.decode('utf8')

			# 同步发邮件
			# subject = '天天生鲜主题'
			# message = ''
			# html_message = '<h1>欢迎成为天天生鲜会员!</h1>请点击以下链接激活账户<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (token, token)
			# from_email = settings.EMAIL_FROM
			# receiver = [email]
			# send_mail(subject, message, from_email, receiver, html_message=html_message)
			# sleep(5)

			# 异步使用selery 发邮件
			send_register_active_email.delay(email, user_name, token)

			return redirect(reverse('goods:index'))


# user/active/<str:token>  邮箱登录地址
def active(request, token):
	serializer = Serializer(settings.SECRET_KEY, 3600)
	try:
		info = serializer.loads(token)
		print(token)
		user_id = info['user_id']
		user = User.objects.get(id=user_id)
		user.is_active = 1
		user.save()
		return redirect(reverse('user:login'))
	except SignatureExpired:
		return HttpResponse('注册时间过期')


# user/login
class LoginView(View):

	def get(self, request):
		# 判断是否记住用户名：
		if 'username' in request.COOKIES:
			username = request.COOKIES.get('username')
			checked = 'checked'
		else:
			username = ''
			checked = ''
		return render(request, 'login.html', context={'username': username, 'checked': checked})

	def post(self, request):
		username = request.POST.get('username')
		pwd = request.POST.get('pwd')

		if not all([username, pwd]):
			return render(request, 'login.html', {'errmsg': '用户名或密码不完整'})

		user = authenticate(username=username, password=pwd)  # 内置了加解密方法
		if user is not None:
			if user.is_active:
				login(request, user)                         # 记录用户登录状态, 默认使用内置db存储session，修改成为redis存储session

				# 获取登录后要调到的地址, 默认跳转到首页
				next_url = request.GET.get('next', reverse('goods:index'))

				# 跳转到首页
				response = redirect(next_url)  # HttpResponseRedirect
				remember = request.POST.get('remember')      # 获取表单remember

				# 判断是否要记住用户名
				if remember == 'on':
					# 记住用户名
					response.set_cookie('username', username, max_age=60*60*24*7)
				else:
					# 删除用户名
					response.delete_cookie('username')

				# 返回response
				return response
			else:                                            # 用户未激活
				return render(request, 'login.html', {'errmsg': '账户未激活'})
		else:                                                # 用户名或密码错误
			return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


# user/logout
class LogoutView(View):

	def get(self, request):
		# 清除用户的session信息
		logout(request)
		return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin, View):

	def get(self, request):

		# 进行欢迎信息的显示
		# 如果用户登录-> User 类的一个实例; 如果用户未登录-> AnonymousUser 类的一个实例
		# request.user.is_authenticated()   返回True or False
		# 除了自身传递的模板变量，Django框架也会把 user = request.user也传给模板文件, 传递的变量叫 user, 用于base.html 进行欢迎信息的修改

		# 获取用户的个人信息
		user = request.user
		address = Address.objects.get_default_address(user)

		# 获取用户的历史浏览信息
		# 此处参数应该和settings里的一致.
		# 方法1：
		# from redis import StrictRedis
		# sr = StrictRedis(host='localhost', port=6379, db=1)
		# 方法2：
		from django_redis import get_redis_connection
		con = get_redis_connection('default')

		history_key = 'history_%d' % user.id

		# 获取用户最新浏览的五个商品的id
		sku_ids = con.lrange(history_key, 0, 4)

		# 从数据库中查询用户浏览商品的具体信息
		goods_li = []
		for sku_id in sku_ids:
			goods = GoodsSKU.objects.get(id=sku_id)
			goods_li.append(goods)

		context = {
			'page': 'user',
			'address': address,
			'goods_li': goods_li,
			'user': user,
		}

		# 由于Django默认传了user，所以可以不用传到模板文件
		return render(request, 'user_center_info.html', context=context)


# /user/order/<int:page>
class UserOrderView(LoginRequiredMixin, View):
	"""用户中心-订单页"""

	def get(self, request, page):
		"""显示"""
		# 获取用户的订单信息
		user = request.user
		orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

		# 遍历获取订单商品的信息
		for order in orders:
			# 根据order_id查询订单商品信息
			order_skus = OrderGoods.objects.filter(order_id=order.order_id)

			# 遍历order_skus计算商品的小计
			for order_sku in order_skus:
				# 计算小计
				amount = order_sku.count * order_sku.price
				# 动态给order_sku增加属性amount,保存订单商品的小计
				order_sku.amount = amount

			# 动态给order增加属性，保存订单状态标题
			order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
			# 动态给order增加属性，保存订单商品的信息
			order.order_skus = order_skus

		# 分页
		paginator = Paginator(orders, 1)

		# 获取第page页的内容
		try:
			page = int(page)
		except Exception as e:
			page = 1

		if page > paginator.num_pages:
			page = 1

		# 获取第page页的Page实例对象
		order_page = paginator.page(page)

		# todo: 进行页码的控制，页面上最多显示5个页码
		# 1.总页数小于5页，页面上显示所有页码
		# 2.如果当前页是前3页，显示1-5页
		# 3.如果当前页是后3页，显示后5页
		# 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
		num_pages = paginator.num_pages
		if num_pages < 5:
			pages = range(1, num_pages + 1)
		elif page <= 3:
			pages = range(1, 6)
		elif num_pages - page <= 2:
			pages = range(num_pages - 4, num_pages + 1)
		else:
			pages = range(page - 2, page + 3)

		# 组织上下文
		context = {
			'order_page': order_page,
			'pages': pages,
			'page': 'order',
		}

		# 使用模板
		return render(request, 'user_center_order.html', context)


# /user/address
class UserAddressView(LoginRequiredMixin, View):

	def get(self, request):

		# 获取用户的默认收货地址
		user = request.user

		# try:
		# 	address = Address.objects.get(user=user, is_default=True)  # models.Manager
		# except Address.DoesNotExist:
		# 	# 不存在默认收货地址
		# 	address = None
		address = Address.objects.get_default_address(user)

		# 使用模板
		return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

	def post(self, request):
		# 接收数据
		receiver = request.POST.get('receiver')
		addr = request.POST.get('addr')
		zip_code = request.POST.get('zipcode')
		phone = request.POST.get('phone')

		# 数据校验
		if not all([receiver, addr, phone]):
			return render(request, 'user_center_site.html', context={'errmsg': '数据不完整'})
		if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
			return render(request, 'user_center_site.html', context={'errmsg': '邮编格式不正确'})

		# 业务处理：地址添加
		# 如果用户已存在默认收货地址，则添加的地址不作为默认收货地址，否则作为默认收货地址
		# 获取登录用户对应的User对象，能进这个页面，说明User存在
		user = request.user

		# try:
		# 	# 第一种方法：
		# 	# addresses = User.objects.get(pk=user.id).address_set    # User存在, 就可得到当前用户所有的地址
		# 	# address = addresses.get(is_default=True)
		# 	# 第二种方法： 简洁
		# 	address = Address.objects.get(user=user, is_default=True)
		# except Address.DoesNotExist:
		# 	address = None

		address = Address.objects.get_default_address(user)

		if address:
			is_default = False
		else:
			is_default = True

		# 添加地址
		Address.objects.create(user=user, receiver=receiver, addr=addr, zip_code=zip_code, phone=phone, is_default=is_default)
		# 返回应答,刷新地址页面
		return redirect(reverse('user:address'))  # get请求方式