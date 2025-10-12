from src.core.application.ports.outbound import PaymentDetailsProviderPort
from src.infrastructure.config import settings


class ConfigPaymentDetailsProvider(PaymentDetailsProviderPort):
    def __init__(self):
        self.credentials = settings.PAYMENT_DETAILS

    def get(self) -> str:
        return self.credentials