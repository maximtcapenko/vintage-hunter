DEFAULT_PAGE_SIZE = 50
SEARCH_RESULTS_LIMITS = 25


def is_staff(user):
    return user.is_authenticated and user.is_staff

def is_not_staff(user):
    return user.is_authenticated and not user.is_staff