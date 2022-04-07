
import json
from os import mkdir, path
from typing import Dict

from core.exceptions import PostNotExitsError, PostTitleDuplicateError

from .models import ForumFile, ForumMessage, ForumModelEncoder, ForumPost


class ForumHandler:
    '''Handler forum'''
    file_path: str
    data_path: str

    pid_dict: Dict[int, ForumPost] = {}
    title_dict: Dict[str, ForumPost] = {}

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

                        forum_post = ForumPost(
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

    def __fetch_thread(self, title: str = None, pid: int = None):
        if title and title in self.title_dict:
            return self.title_dict[title]

        if pid and pid in self.pid_dict:
            return self.pid_dict[pid]

        raise PostNotExitsError(404, f'Post {title} not found')

    def create_thread(self, title, user):
        if title in self.title_dict:
            raise PostTitleDuplicateError(
                400, f'Thread {title} is already exist')

        no = self.current_no
        post = ForumPost(no, title, user, {})

        self.current_no += 1
        self.pid_dict[no] = post
        self.title_dict[title] = post

        self.__save_db()

        return post

    def list_threads(self):
        ...

    def post_message(self, title, user, message):
        post = self.__fetch_thread(title, None)

        ...

    def post_message_no(self, pid, user, message):
        post = self.__fetch_thread(None, pid)

    def delete_message(self, title, mid, user):
        post = self.__fetch_thread(title, None)

    def delete_message_no(self, pid, mid, user):
        post = self.__fetch_thread(None, pid)

    def read_thread(self, title):
        post = self.__fetch_thread(title, None)

    def read_thread_no(self, pid):
        post = self.__fetch_thread(None, pid)
