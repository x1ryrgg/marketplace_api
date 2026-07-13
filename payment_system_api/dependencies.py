from typing import Optional

from payment_system_api.models import History
from usercontrol_api.models import User, Coupon
from decimal import Decimal


def _apply_discount_to_order(
    user: User, total_price: Decimal, coupon: Optional[Coupon] = None
) -> Decimal:
    """Применяет скидку пользователя к общей стоимости заказа"""
    discount = History.objects.calculate_discount(user)

    if coupon:
        discount += Decimal(coupon.discount / 100)

    discounted_price = total_price * Decimal(1 - discount)
    return discounted_price
