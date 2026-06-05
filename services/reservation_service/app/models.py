from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class HotelTier(str, Enum):
    tier1 = "tier1"
    tier2 = "tier2"
    tier3 = "tier3"


class ReservationRequest(BaseModel):
    ota_partner: str = Field(..., examples=["Booking.com"])
    hotel_chain_id: str = Field(..., examples=["hotel_alpha"])
    property_id: str = Field(..., examples=["DAL-100"])
    hotel_tier: HotelTier
    guest_name: str
    room_type: str = Field(..., examples=["KING"])
    check_in: date
    check_out: date
    guest_count: int = Field(..., ge=1, le=8)
    total_amount: Decimal = Field(..., gt=0)


class ReservationResponse(BaseModel):
    confirmation_id: str
    status: str
    queue_stream: str

