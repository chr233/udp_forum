
from json import JSONEncoder
from typing import Dict


class ForumMessage:
    mid: int
    author: str
    message: str

    def __init__(self, no: int, author: str, message: str) -> None:
        self.mid = no
        self.author = author
        self.message = message


class ForumPost:
    pid: int
    title: str
    author: str
    next_mid: int
    messages: Dict[int, ForumMessage]

    def __init__(self, pid: int, title: str, author: str, next_mid: int, messages: Dict[int, ForumMessage]) -> None:
        self.pid = pid
        self.title = title
        self.author = author
        self.next_mid = next_mid
        self.messages = messages


class ForumModelEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ForumPost):
            return {
                'title': obj.title,
                'author': obj.author,
                'next_mid': obj.next_mid,
                'messages': obj.messages,
            }
        elif isinstance(obj, ForumMessage):
            return {
                'author': obj.author,
                'message': obj.message,
            }
        return JSONEncoder.default(self, obj)
