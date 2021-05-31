# Assign(targets=[Name(id='heystring', ctx=Store())], value=Str(s='1'))
heystring = "1"
# Assign(targets=[Name(id='heyint', ctx=Store())], value=Num(n=2))
heyint = 2
# Assign(targets=[Name(id='heydict', ctx=Store())], value=Dict(keys=[Str(s='heydictvar')], values=[Str(s='dict_string_value')]))
# Dict(keys=[Str(s='heydictvar')], values=[Str(s='dict_string_value')])
# Dict(keys=[Str(s='heydictvar'), Str(s='seconddictvar')], values=[Str(s='dict_string_value'), Str(s='another value')])
heydict = {
    'heydictvar': 'dict_string_value',
    'seconddictvar': 'another value',
    'nested': {
        'bird': 'house',
    },
}
# FunctionDef(name='heyfunction', args=arguments(args=[arg(arg='named_arg', annotation=None), arg(arg='password', annotation=None)], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[Str(s='hunter2')]), body=[Return(value=BinOp(left=Num(n=1), op=Add(), right=Num(n=1)))], decorator_list=[], returns=None)
def heyfunction(named_arg, password="hunter2"):
    return 1 + 1
# Assign(targets=[Name(id='result', ctx=Store())], value=Call(func=Name(id='heyfunction', ctx=Load()), args=[Num(n=42)], keywords=[keyword(arg='password', value=Str(s='2hunter'))]))
# Call(func=Name(id='heyfunction', ctx=Load()), args=[Num(n=42)], keywords=[keyword(arg='password', value=Str(s='2hunter'))])
result = heyfunction(42, password="2hunter")

class SomeClass():

    def __init__(self):
        self.somevar1 = None
        self.username = None
        return

myclass = SomeClass()
# Assign(targets=[Attribute(value=Name(id='myclass', ctx=Load()), attr='somevar1', ctx=Store())], value=Str(s='password'))
myclass.somevar1 = "password"
# Assign(targets=[Attribute(value=Name(id='myclass', ctx=Load()), attr='username', ctx=Store())], value=Str(s='root'))
myclass.username = "root"
