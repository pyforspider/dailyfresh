import os
from time import sleep

from celery import Celery

from django.conf import settings
from django.core.mail import send_mail

# 任务处理端增加以下代码：
"""1. 发送邮件任务"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
django.setup()
"""2. 生成静态页面任务, 注意该任务必须在加载了设置了环境初始化之后才能引入该模块，否则报错"""
from django.template import loader
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


# 创建celery对象
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')  # 第一个参数随便写， 一般写项目主路径的 'celery_tasks.tasks'

# 任务
@app.task
def send_register_active_email(to_email, username, token):
	subject = '天天生鲜主题'
	message = ''
	html_message = '<h1>%s，欢迎您成为天天生鲜会员!</h1>请点击以下链接激活账户<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (username, token, token)
	from_email = settings.EMAIL_FROM
	receiver = [to_email]
	send_mail(subject, message, from_email, receiver, html_message=html_message)
	sleep(5)


@app.task
def generate_static_index_html():

	# 先睡两秒，以防数据库更新太慢，数据还没更新就已经生成页面
	sleep(5)
	# 获取首页商品类型信息
	goods_types = GoodsType.objects.all()
	# 获取首页商品轮播信息
	goods_banner = IndexGoodsBanner.objects.all().order_by('index')
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
	# 获取购物车商品数目
	cart_count = 0

	context = {
		'goods_types': goods_types,
		'goods_banner': goods_banner,
		'promotion_banner': promotion_banner,

		'cart_count': cart_count,
	}

	# 使用模板
	# 1. 加载模板文件，返回模板对象
	temp = loader.get_template('static_index.html')
	# 2. 模板渲染
	static_index_html = temp.render(context)
	# 3. 生成首页对应的静态模板文件
	save_path = os.path.join(settings.BASE_DIR, 'templates/generated_static_index.html')
	with open(save_path, 'w', encoding='utf-8') as fb:
		fb.write(static_index_html)


	# # 使用模板
	# # 1. 加载模板文件，返回模板对象
	# temp2 = loader.render_to_string('static_index.html')
	# # 3. 生成首页对应的静态模板文件
	# save_path = os.path.join(settings.BASE_DIR, 'static/static_index.html')
	# with open(save_path, 'w', encoding='utf-8') as fb:
	# 	fb.write(temp2)


# 终端测试
# from celery_tasks.tasks import generate_static_index_html
# generate_static_index_html.delay()
# generate_static_index_html()


# from celery_tasks.tasks import send_register_active_email
# send_register_active_email.delay('1303292392@qq.com', 'shaojian12341', 'asfasf')
