"""Replaceable adapters for order alerts sent to staff messaging providers."""
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone

from .models import Order

logger = logging.getLogger(__name__)


def _order_message(order):
    address = order.address_snapshot
    coordinates = (address.get("latitude"), address.get("longitude"))
    map_url = f"https://www.openstreetmap.org/?mlat={coordinates[0]}&mlon={coordinates[1]}#map=15/{coordinates[0]}/{coordinates[1]}" if all(coordinates) else "Location pin unavailable"
    items = []
    for item in order.items.all():
        options = ", ".join(option.name for option in item.options.all())
        line = f"• {item.quantity} {item.unit} {item.product_name}"
        if options:
            line += f" ({options})"
        items.append(line)
    address_text = ", ".join(str(address.get(key) or "") for key in (
        "address_line1", "address_line2", "landmark", "city", "state", "postal_code", "country_code",
    )).strip(", ")
    fulfillment = "Preorder" if order.is_preorder else "Order now"
    if order.scheduled_for:
        fulfillment += f" · {timezone.localtime(order.scheduled_for).strftime('%d %b %Y, %I:%M %p %Z')}"
    lines = [
        f"New order #{order.pk} — {order.get_status_display()}",
        f"Customer: {order.user.username} · {order.user.email} · {order.user.phone_number or 'No profile phone'}",
        f"Fulfilment: {fulfillment}",
        "Items:", *(items or ["• (no items)"]),
        f"Subtotal: INR {order.subtotal:.2f}",
        f"GST: INR {order.gst_total:.2f}",
        f"Delivery: INR {order.delivery_fee:.2f}",
        f"Total: INR {order.total:.2f}",
        f"Deliver to: {address.get('recipient_name') or ''} · {address.get('phone_number') or ''}",
        f"Address: {address_text or 'Not provided'}",
        f"Coordinates: {coordinates[0] or '—'}, {coordinates[1] or '—'}",
        f"Map: {map_url}",
    ]
    if order.delivery_distance_km is not None:
        lines.insert(-4, f"Straight-line distance: {order.delivery_distance_km:.2f} km · first {order.delivery_free_distance_km:.2f} km free · INR {order.delivery_fee_per_km:.2f}/km thereafter")
    if order.customer_note:
        lines.append(f"Customer note: {order.customer_note}")
    # Telegram allows 4096 characters; leave room for provider-side formatting.
    return "\n".join(lines)[:3900]


def _load_order(order_id):
    return Order.objects.select_related("user").prefetch_related("items__options").get(pk=order_id)


def send_admin_order_telegram(order_id):
    """Send a plain-text order alert with address, coordinates, and map URL."""
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    if not token or not chat_id:
        logger.warning("Telegram order notifications are enabled but bot credentials are incomplete.")
        return False
    payload = {"chat_id": chat_id, "text": _order_message(_load_order(order_id)), "disable_web_page_preview": True}
    try:
        request = Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            return response.status == 200 and result.get("ok") is True
    except (HTTPError, URLError, TimeoutError, ValueError):
        # The Telegram bot token is embedded in its endpoint URL. Never log the URL or exception.
        logger.warning("Telegram order notification failed for order_id=%s", order_id)
        return False


def send_admin_order_notification(order_id):
    """Select the configured provider; provider SDK/API details stay behind adapters."""
    provider = settings.ORDER_NOTIFICATION_PROVIDER
    if provider == "telegram":
        return send_admin_order_telegram(order_id)
    if provider == "disabled":
        return False
    logger.error("Unsupported order notification provider configured.")
    return False
