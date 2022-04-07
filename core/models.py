
from json import JSONEncoder
from typing import Dict


class ForumMessage:
    mid: int
    author: str
    message: str

    def __init__(self, mid: int, author: str, message: str) -> None:
        self.mid = mid
        self.author = author
        self.message = message


class ForumFile:
    fid: int
    uploader: str
    name: str

    def __init__(self, fid: int, uploader: str, name: str) -> None:
        self.fid = fid
        self.uploader = uploader
        self.name = name


class ForumPost:
    pid: int
    title: str
    author: str
    next_mid: int
    next_fid: int
    messages: Dict[int, ForumMessage]
    files: Dict[int, ForumFile]

    def __init__(self, pid: int, title: str, author: str, next_mid: int, next_fid: int, messages: Dict[int, ForumMessage], files: Dict[int, ForumFile]) -> None:
        self.pid = pid
        self.title = title
        self.author = author
        self.next_mid = next_mid
        self.next_fid = next_fid
        self.messages = messages
        self.files = files


class ForumModelEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ForumPost):
            return {
                'title': obj.title,
                'author': obj.author,
                'next_mid': obj.next_mid,
                'next_fid': obj.next_fid,
                'messages': obj.messages,
            }
        elif isinstance(obj, ForumMessage):
            return {
                'author': obj.author,
                'message': obj.message,
            }

        elif isinstance(obj, ForumFile):
            return {
                'uploader': obj.uploader,
                'name': obj.name
            }

        return JSONEncoder.default(self, obj)
