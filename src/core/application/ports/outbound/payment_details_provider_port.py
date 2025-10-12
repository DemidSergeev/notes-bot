from typing import Protocol

class PaymentDetailsProviderPort(Protocol):
    def get(self) -> str:
        raise NotImplementedError