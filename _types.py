from typing import NotRequired, TypedDict

from bson import ObjectId


class Item(TypedDict):
    name: str
    price: int


class Log(TypedDict):
    _id: NotRequired[ObjectId]
    user_id: str
    username: str
    item: Item
    paypal_email: NotRequired[str]
    cashapp_tag: NotRequired[str]
    venmo_username: NotRequired[str]
    stripe_email: NotRequired[str]
    btc_address: NotRequired[str]
    ltc_address: NotRequired[str]
    eth_address: NotRequired[str]


class Stock(TypedDict):
    _id: NotRequired[ObjectId]
    item: str
    quantity: int
    price: int
