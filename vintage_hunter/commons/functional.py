from functools import cached_property


DEFAULT_PAGE_SIZE = 50
SEARCH_RESULTS_LIMITS = 25


def is_staff(user):
    return user.is_authenticated and user.is_staff

def is_not_staff(user):
    return user.is_authenticated and not user.is_staff

def add_to_class(cls, func, name):
    func_property = cached_property(func)
    cls.add_to_class(name, func_property)
    func_property.__set_name__(cls, name)