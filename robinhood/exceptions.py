class NotFound(Exception):
    pass

class NotLoggedIn(Exception):
    pass

class MfaRequired(Exception):
    pass

class BadRequest(Exception):
    pass

class TooManyRequests(Exception):
    pass

class Forbidden(Exception):
    pass
