class ConcException(Exception):
    def __init__(self, message, eqn):
        super().__init__(message)
        self.eqn = eqn


class ThmFormatException(Exception):
    def __init__(self, message, eqn):
        super().__init__(message)
        self.thm = eqn


class SimplifyException(Exception):
    def __init__(self, message, eqn):
        super().__init__(message)
        self.thm = eqn
