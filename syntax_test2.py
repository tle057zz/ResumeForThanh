def returns_dict(func):
    # Complete the returns_dict() decorator
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        assert type(result) == list
        return result
    return wrapper


@returns_dict
def foo(value):
    return value


try:
    print(foo([1, 2, 3]))
except AssertionError:
    print('foo() did not return a dict!')