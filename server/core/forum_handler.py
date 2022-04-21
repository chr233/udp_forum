
import json
from base64 import b64decode
from os import mkdir, path
from typing import Dict, Tuple

from core.exceptions import (FileContentDecodeError, FileIOError,
                             FileNameDuplicateError, FileNotExitsError,
                             MessageNotExitsError, PermissionDeniedError,
                             PostNotExitsError, PostTitleDuplicateError)
from core.utils import package_file,remove_dir_recursive

from .models import ForumFile, ForumMessage, ForumModelEncoder, ForumThread


class ForumHandler:
    '''Handler forum'''
    file_path: str
    data_path: str

    pid_dict: Dict[int, ForumThread] = {}
    title_dict: Dict[str, ForumThread] = {}

    current_no = 0

    def __init__(self, file_path: str, data_path: str):
        self.file_path = file_path
        self.data_path = data_path

        self.__load_db()
        self.__save_db()

    def __load_db(self):
        try:
            self.pid_dict = {}
            self.title_dict = {}
            max_no = 0

            if not path.exists(self.file_path):
                open(self.file_path, 'a', encoding='utf-8').close()

            if not path.exists(self.data_path):
                mkdir(self.data_path)

            with open(self.file_path, 'r', encoding='utf-8') as f:
                jd = json.load(f)
                if not isinstance(jd, dict):
                    jd = {}

                for p_id, post in jd.items():
                    try:
                        p_id = int(p_id)

                        if p_id > max_no:
                            max_no = p_id

                        p_title = post['title']
                        p_author = post['author']
                        p_next_mid = max(int(post['next_mid']), 1)
                        p_next_fid = max(int(post['next_fid']), 1)
                        p_messages = post['messages']
                        p_files = post['files']

                        if not isinstance(p_messages, dict):
                            p_messages = {}

                        if not isinstance(p_files, dict):
                            p_files = {}

                        messages = {}
                        for m_id, reply in p_messages.items():
                            try:
                                m_id = int(m_id)
                                if m_id > p_next_mid:
                                    p_next_mid = m_id + 1
                                r_author = reply['author']
                                r_message = reply['message']
                                messages[m_id] = ForumMessage(
                                    m_id, r_author, r_message
                                )

                            except (KeyError, ValueError) as e:
                                print(e)

                        files = {}
                        for f_id, file in p_files.items():
                            try:
                                f_id = int(f_id)
                                if f_id > p_next_fid:
                                    p_next_fid = f_id + 1
                                f_uploader = file['uploader']
                                f_name = file['name']
                                files[f_id] = ForumFile(
                                    f_id, f_uploader, f_name
                                )

                            except (KeyError, ValueError) as e:
                                print(e)

                        forum_post = ForumThread(
                            p_id, p_title, p_author,
                            p_next_mid, p_next_fid,
                            messages, files
                        )
                        self.pid_dict[p_id] = forum_post
                        self.title_dict[p_title] = forum_post

                    except (KeyError, ValueError) as e:
                        print(e)

            self.current_no = max_no + 1

        except Exception as e:
            print(e)

    def __save_db(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self.pid_dict, f,
                    cls=ForumModelEncoder,
                    sort_keys=True,
                    indent=2,
                )

        except Exception as e:
            print(e)

    def __fetch_thread(self, title: str = None) -> ForumThread:
        if title and title in self.title_dict:
            return self.title_dict[title]

        try:
            pid = int(title)
            if pid and pid in self.pid_dict:
                return self.pid_dict[pid]
        except ValueError:
            pass

        raise PostNotExitsError(404, f'Thread {title} not found')

    def __fetch_thread_message(self, title: str, mid: int) -> Tuple[ForumThread, ForumMessage]:
        thread = self.__fetch_thread(title)

        if mid in thread.messages:
            return (thread, thread.messages[mid])

        raise MessageNotExitsError(
            404, f'Message id {mid} in thread {title} not found')

    def __fetch_thread_file(self, title: str, name: str) -> ForumFile:
        thread = self.__fetch_thread(title)

        for file in thread.files.values():
            if file.name == name or file.fid == name:
                return file

        raise FileNotExitsError(
            404, f'File {name} in thread {title} not found')

    def create_thread(self, title, user) -> ForumThread:
        if title in self.title_dict:
            raise PostTitleDuplicateError(
                400, f'Thread {title} is already exist')

        pid = self.current_no
        new_post = ForumThread(pid, title, user, 1, 1, {}, {})

        self.current_no += 1
        self.pid_dict[pid] = new_post
        self.title_dict[title] = new_post

        self.__save_db()

        return f'Thread {title} created'

    def delete_thread(self, title: str, user: str) -> str:
        thread = self.__fetch_thread(title)

        if user != thread.author:
            raise PermissionDeniedError(
                403, 'The thread belongs to another user and cannot be edited')

        self.pid_dict.pop(thread.pid, None)
        self.title_dict.pop(thread.title, None)

        next_fid = 1
        pid_dict = {}
        title_dict = {}
        for i, th in enumerate(self.pid_dict.values(), 1):
            th.pid = i
            pid_dict[i] = th
            title_dict[title] = th
            next_fid += 1

        self.pid_dict = pid_dict
        self.title_dict = title_dict
        self.current_no = next_fid

        self.__save_db()
        
        fold_path = path.join(self.data_path, title)
        if path.exists(fold_path):
            remove_dir_recursive(fold_path)

        return f'Thread {thread.title} deleted'

    def list_threads(self) -> str:
        lines = ['ID | Thread Title | Author']

        ids = sorted(self.pid_dict.keys())

        if not ids:
            lines.append('There is no thread in this thread')
        else:
            for pid in ids:
                post = self.pid_dict.get(pid, None)
                if not post:
                    continue
                lines.append(
                    f'{str(pid).ljust(2)} | {post.title.ljust(12)} | {post.author}')

        return '\n'.join(lines)

    def read_thread(self, title: str) -> str:
        thread = self.__fetch_thread(title)

        lines = ['ID | Message']

        msgs = thread.messages.values()

        if not msgs:
            lines.append('There is no message in this thread')
        else:
            for msg in msgs:
                lines.append(
                    f'{str(msg.mid).ljust(2)} | {msg.author}: {msg.message}')

        files = thread.files.values()

        if files:
            lines.append('')
            lines.append('ID | File Name')

            for file in files:
                lines.append(
                    f'{str(file.fid).ljust(2)} | {file.uploader}: {file.name}')

        return '\n'.join(lines)

    def post_message(self, title: str, message: str, user: str) -> str:
        thread = self.__fetch_thread(title)

        mid = thread.next_mid
        msg = ForumMessage(mid, user, message)
        thread.messages[mid] = msg
        thread.next_mid += 1

        self.__save_db()

        return f'Message posted to {thread.title} thread'

    def edit_message(self, title: str, mid: str, message: str, user: str) -> str:
        thread, msg = self.__fetch_thread_message(title, mid)

        if user != msg.author:
            raise PermissionDeniedError(
                403, f'The thread belongs to another user and cannot be edited')

        msg.message = message
        thread.messages[mid] = msg

        self.__save_db()

        return 'The message has been edited'

    def delete_message(self, title: str, mid: str, user: str) -> str:
        thread, msg = self.__fetch_thread_message(title, mid)

        if user != msg.author:
            raise PermissionDeniedError(
                403, f'The thread belongs to another user and cannot be edited')

        thread.messages.pop(msg.mid, None)

        next_mid = 1
        messages = {}
        for i, msg in enumerate(thread.messages.values(), 1):
            msg.mid = i
            messages[i] = msg
            next_mid += 1

        thread.messages = messages
        thread.next_mid = next_mid

        self.__save_db()

        return 'The message has been deleted'

    def upload_file(self, title: str, file_name: str, content: str, user: str) -> str:
        thread = self.__fetch_thread(title)

        for file in thread.files.values():
            if file_name == file.name:
                raise FileNameDuplicateError(
                    400, f'File {file_name} is already exist')

        try:
            raw = b64decode(content.encode('utf-8'))
        except Exception:
            raise FileContentDecodeError(
                400, f'File {file_name} content decode error')

        fold_path = path.join(self.data_path, title)
        if not path.exists(fold_path):
            mkdir(fold_path)

        file_path = path.join(fold_path, file_name)
        try:
            with open(file_path, 'wb') as f:
                f.write(raw)
        except Exception:
            raise FileIOError(500, f'Can not write file {file_name}')

        fid = thread.next_fid
        file = ForumFile(fid, user, file_name)
        thread.files[fid] = file
        thread.next_fid += 1

        self.__save_db()

        return f'File {file_name} uploaded to {title} thread'

    def download_file(self, title: str, file_name: str) -> str:
        file = self.__fetch_thread_file(title, file_name)

        file_path = path.join(self.data_path, title, file.name)

        try:
            name, body = package_file(file_path)
        except Exception:
            raise FileIOError(404, f'Can not read file {file_name}')

        return body
