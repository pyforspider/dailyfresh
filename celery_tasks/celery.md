# ʹ��˵��

* ������Ŀ�ļ��� `dailyfresh` ��linux������(��Ҫ��װ��celery)��
* ��д�ļ�tasks.py �е�HOST��ַ Ϊ linux������ip��ַ��(���񷢳��˼��������˵�tasks.py��Ҫ�޸�)
* linux������Ŀ�ļ��У�ִ������ `celery -A celery_tasks.tasks worker --pool=solo -l info`
* �������񷢳��߶˼����첽ִ���ʼ���������


celery -A celery_tasks.tasks worker -l info

celery -A celery_tasks.tasks worker --pool=solo -l info

