def juntar(a, b):
    return str(a) + str(b)


class Conta:
    def __init__(self, saldo):
        self.saldo = saldo

    def sacar(self, valor):
        self.saldo -= valor
        return self.saldo
