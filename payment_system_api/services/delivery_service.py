import enum
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from payment_system_api.models import Delivery, DeliveryType, History
from product_control_api.models import ProductVariant
from usercontrol_api.models import User


class DeliveryOption(enum.Enum):
    ACCEPT = "accept"
    CANCEL = "cancel"


class DeliveryService(ABC):
    """
    Абстрактный класс для управления жизненным циклом доставки.
    """
    def __init__(self, delivery: Delivery, user: User):
        self.delivery = delivery
        self.user = user

    @abstractmethod
    def process_option(self, option: DeliveryOption) -> Dict:
        """
        Обработка выбора пользователя ("accept" - принять, "cancel" - отменить).
        """
        pass


class DefaultDeliveryService(DeliveryService):
    """
    Стандартная логика доставки:
    - При отмене "в пути" деньги возвращаются, товар едет на склад.
    - При отмене "уже доставлено" деньги СГОРАЮТ (политика невозврата), товар едет на склад.
    """

    def process_option(self, option: DeliveryOption) -> Dict:
        if option not in [DeliveryOption.ACCEPT, DeliveryOption.CANCEL]:
            raise ValidationError(_("Недопустимое действие. Доступно: 'accept' или 'cancel'."))

        with transaction.atomic():
            product = get_object_or_404(ProductVariant.objects.select_for_update(),
                                        pk=self.delivery.product_id)

            if self.delivery.status == DeliveryType.ON_THE_WAY:
                if option == DeliveryOption.CANCEL:
                    return self._cancel_on_the_way(product)
                raise ValidationError(_("Товар еще не доставлен."))

            if option == DeliveryOption.ACCEPT:
                return self._accept_delivery()
            else:
                return self._cancel_after_arrival(product)

    def _accept_delivery(self):
        """
        Принятие товара | option = accept
        """
        History.objects.create(
            user=self.user,
            product=self.delivery.product,
            user_price=self.delivery.user_price,
            quantity=self.delivery.quantity,
            status=DeliveryType.DELIVERED,
        )
        self.delivery.delete()

        return {
            "status": "delivered",
            "refunded_amount": "0.00",
        }

    def _cancel_after_arrival(self, product: ProductVariant):
        """
        Отказ от товара после прибытия в пункт выдачи | option = cancel
        """
        product.quantity += self.delivery.quantity
        product.save(update_fields=["quantity"])

        History.objects.create(
            user=self.user,
            product=self.delivery.product,
            user_price=self.delivery.product.price,
            quantity=self.delivery.quantity,
            status=DeliveryType.DENIED,
        )
        self.delivery.delete()

        return {
            "status": "cancelled_after_arrival",
            "refunded_amount": "0.00",
        }

    def _cancel_on_the_way(self, product: ProductVariant):
        """
        Отказ от товара ДО прибытия в пункт выдачи | option = cancel
        """
        locked_user = User.objects.select_for_update().get(pk=self.user.id)
        locked_user.balance += self.delivery.user_price
        locked_user.save(update_fields=["balance"])

        product.quantity += self.delivery.quantity
        product.save(update_fields=["quantity"])

        History.objects.create(
            user=locked_user,
            product=self.delivery.product,
            user_price=self.delivery.product.price,
            quantity=self.delivery.quantity,
            status=DeliveryType.DENIED,
        )

        refund_value = self.delivery.user_price
        self.delivery.delete()

        return {
            "status": "cancelled_on_the_way",
            "refunded_amount": str(refund_value.quantize(Decimal("0.01"))),
        }
