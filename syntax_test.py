def f(*args):
    print(args)

f(1, 2, 3)
# args = (1, 2, 3)

def g(**kwargs):
    print(kwargs)

g(name="Nam", age=25)
# kwargs = {'name': 'Nam', 'age': 25}
def returns(return_type):
    # Complete the returns() decorator
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            assert type(result) == return_type
            return result

        return wrapper

    return decorator


@returns(dict)
def foo(value):
    return value


try:
    print(foo([1, 2, 3]))
except AssertionError:
    print('foo() did not return a dict!')



