1. 类继承

        super() -> same as super(__class__, <first argument>)
        super(type, obj) -> bound super object; requires isinstance(obj, type)
        
        class Person：
            def __init__(self, name, age):
                self.name = name
                self.age = age
                
            def eat(self, food):
                print('%s is eating %s' % (self.name, self.food))
        
        class Employee(Person):
            def __init__(self, name, age, salary, manager):
                super().__init__(name. age)                      # 通过super()继承父类属性
                self.salary = salary                             # 子类自定义的属性
                self.manager = manager           
        等同于：
        class Employee(Person):
            def __init__(self, name, age, salary, manager):
                super(Employee, self).__init__(name, age)        # 使用的是第二种super(type, object)，多了一层isinstance  
                self.salary = salary                             # 子类自定义的属性
                self.manager = manager
            
            def eat(self, food):
                super().eat(food)                                       # 通过super()调用父类eat方法
                print('%s is eating %s' % (self.name, food))   # 子类新增动作

2. 类中__str__()方法，友好化显示实例对象

        class Person2:
            def __init__(self, name, age):
                self.name = name
                self.age = age
        
            def eat(self, food):
                print('%s is eating an amount of %s' % (self.name, food))
        
            def __str__(self):
                msg = self.name + "'s age is " + str(self.age)
                return msg        
        
        p = Person2('小丁', 30)
        print(p)
        
        














        