# Copyright (C) 2020 - 2021 Divkix. All rights reserved. Source code available under the AGPL.
#
# This file is part of Alita_Robot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from threading import RLock
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
import asyncio
import traceback
from alita.database import MongoDB

INSERTION_LOCK = RLock()
BROADCAST_CHATS = []


class Broadcastlist(MongoDB):
    """Class to blacklist chats where bot will exit."""

    db_name = "broadcast_chats"

    def __init__(self) -> None:
        super().__init__(self.db_name)

    def add_chat(self, chat_id: int):
        with INSERTION_LOCK:
            global BROADCAST_CHATS
            BROADCAST_CHATS.append(chat_id)
            BROADCAST_CHATS.sort()
            return self.insert_one({"_id": chat_id})

    def check_in_db(self, chat_id):
        x = self.find_one({"_id": chat_id})
        return True if x else False

    def remove_chat(self, chat_id: int):
        with INSERTION_LOCK:
            global BROADCAST_CHATS
            BROADCAST_CHATS.remove(chat_id)
            BROADCAST_CHATS.sort()
            return self.delete_one({"_id": chat_id})

    def list_all_chats(self):
        with INSERTION_LOCK:
            try:
                BROADCAST_CHATS.sort()
                return BROADCAST_CHATS
            except Exception:
                all_chats = self.find_all()
                return [chat["_id"] for chat in all_chats]

    def total_users_count(self):
        count = len(list(self.find_all({})))
        return count

    def get_all_chats_from_db(self):
        all_chats = self.find_all()
        return [chat["_id"] for chat in all_chats]

    def get_from_db(self):
        return self.find_all()


async def send_msg(user_id, message):
    try:
        if message.poll:
            await message.forward(chat_id=user_id)
            return 200, None
        else:
            await message.copy(chat_id=user_id)
            return 200, None
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : deactivated\n"
    except UserIsBlocked:
        return 400, f"{user_id} : blocked the bot\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : user id invalid\n"
    except Exception as e:
        return 500, f"{user_id} : {traceback.format_exc()}\n"