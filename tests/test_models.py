from datetime import date
from decimal import Decimal

from services.reservation_service.app.models import HotelTier, ReservationRequest


def test_reservation_request_accepts_valid_payload():
    request = ReservationRequest(
        ota_partner="Booking.com",
        hotel_chain_id="hotel_alpha",
        property_id="DAL-100",
        hotel_tier=HotelTier.tier1,
        guest_name="Devang Patel",
        room_type="KING",
        check_in=date(2026, 7, 1),
        check_out=date(2026, 7, 3),
        guest_count=2,
        total_amount=Decimal("420.50"),
    )

    assert request.hotel_tier == HotelTier.tier1
    assert request.property_id == "DAL-100"

