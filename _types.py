import datetime
from typing import NotRequired, TypedDict

from bson import ObjectId


class Item(TypedDict):
    set: NotRequired[str]
    name: str
    price: int


class Log(TypedDict):
    _id: NotRequired[ObjectId]
    user_id: int
    username: str
    item: Item
    paypal_email: NotRequired[str]
    cashapp_tag: NotRequired[str]
    crypto_address: NotRequired[str]
    created_at: NotRequired[datetime]


class Stock(Item):
    _id: NotRequired[ObjectId]
    quantity: int


class TicketData(TypedDict):
    payment_method: str
    items: list[str]
    subtotal: int
    total: int


class Ticket(TypedDict):
    _id: NotRequired[ObjectId]
    user_id: int
    channel_id: int
    username: str
    category: str
    open: bool
    data: NotRequired[TicketData]
