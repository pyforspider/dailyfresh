# 使用说明

* 拷贝项目文件夹 `dailyfresh` 到linux服务器(需要安装好celery)。
* 改写文件tasks.py 中的HOST地址 为 linux服务器ip地址。(任务发出端及任务工作端的tasks.py需要修改)
* linux进入项目文件夹，执行命令 `celery -A celery_tasks.tasks worker --pool=solo -l info`
* 运行任务发出者端即可异步执行邮件发送任务


celery -A celery_tasks.tasks worker -l info

celery -A celery_tasks.tasks worker --pool=solo -l info

