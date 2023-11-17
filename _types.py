from typing import NotRequired, TypedDict

from bson import ObjectId


class Item(TypedDict):
    name: str
    price: int


class Log(TypedDict):
    _id: NotRequired[ObjectId]
    user_id: int
    username: str
    item: Item
    cashapp_tag: NotRequired[str]
    cashapp_receipt: NotRequired[str]
    paypal_email: NotRequired[str]
    venmo_username: NotRequired[str]
    stripe_email: NotRequired[str]
    btc_address: NotRequired[str]
    ltc_address: NotRequired[str]
    eth_address: NotRequired[str]


class Stock(Item):
    _id: NotRequired[ObjectId]
    quantity: int


class Ticket(TypedDict):
    _id: NotRequired[ObjectId]
    user_id: int
    channel_id: int
    username: str
    category: str
    open: bool
