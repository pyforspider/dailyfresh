8.2.1 mysql事务

1)	事务概念
一组mysql语句，要么执行，要么全不不执行。

2)	事务的特点
1、原子性：一组事务，要么成功；要么撤回。
2、稳定性：有非法数据（外键约束之类），事务撤回。
3、隔离性：事务独立运行。一个事务处理后的结果，影响了其他事务，那么其他事务会撤回。事务的100%隔离，需要牺牲速度。
4、可靠性：软、硬件崩溃后，InnoDB数据表驱动会利用日志文件重构修改。可靠性和高速度不可兼得，innodb_flush_log_at_trx_commit选项决定什么时候吧事务保存到日志里。

3)	事务控制语句
BEGIN或START TRANSACTION；显式地开启一个事务；
COMMIT；也可以使用COMMIT WORK，不过二者是等价的。COMMIT会提交事务，并使已对数据库进行的所有修改称为永久性的；
ROLLBACK；有可以使用ROLLBACK WORK，不过二者是等价的。回滚会结束用户的务，并撤销正在进行的所有未提交的修改；
SAVEPOINT identifier；SAVEPOINT允许在事务中创建一个保存点，一个事务中可以有多个SAVEPOINT；
RELEASE SAVEPOINT identifier；删除一个事务的保存点，当没有指定的保存点时，执行该语句会抛出一个异常；
ROLLBACK TO identifier；把事务回滚到标记点；
