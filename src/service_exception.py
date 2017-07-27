class ServiceException(Exception):
    def __init__(self, message, status_code = 500):
        self.error_message = message
        self.status_code = status_code