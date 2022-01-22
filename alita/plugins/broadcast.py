from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from alita import LOGGER
from alita.bot_class import Alita
from alita.database.broadcast_chats import Broadcastlist, send_msg
from alita.utils.custom_filters import command

import datetime
import asyncio
import string
import aiofiles
import aiofiles.os
import time
import random

# initialise database
db = Broadcastlist()

broadcast_ids = {}

@Alita.on_message(group=10)
async def all_chat_for_br(client: CodeXBotz, message: Message):
    if message.sender_chat:
        chat_id = message.sender_chat.id
    else:
        chat_id = message.from_user.id
    if not db.check_in_db(chat_id):
        db.add_chat(chat_id)


@Alita.on_message(command('total', sudo_cmd=True))
async def get_users(client: CodeXBotz, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text="Counting Users....")
    total_users = await db.total_users_count()
    await msg.edit(text=f"Total user/chat(s) {total_users}")


@CodeXBotz.on_message(command('broadcast', sudo_cmd=True))
async def broadcast(client: CodeXBotz, message: Message):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Cancel"), KeyboardButton("Confirm")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.reply("Send the message that you want to Broadcast")
    response = await client.listen(chat_id=message.chat.id)
    await response.copy(message.chat.id)
    await client.send_message(chat_id=message.chat.id, text="Do you want to send the Broadcast", reply_markup=reply_markup)
    while True:
        confirm = await client.listen(chat_id=message.chat.id)
        if confirm.text == "Cancel":
            break
        elif confirm.text == "Confirm":
            break
        else:
            continue
    if not confirm.text == "Confirm":
        await client.send_message(chat_id=message.chat.id, text=f"Broadcast Cancelled",
                                  reply_markup=ReplyKeyboardRemove())
        return
    await client.send_message(chat_id=message.chat.id, text="Sending Broadcast...",
                              reply_markup=ReplyKeyboardRemove())
    all_users = await db.get_all_users()

    while True:
        broadcast_id = ''.join([random.choice(string.ascii_letters) for i in range(3)])
        if not broadcast_ids.get(broadcast_id):
            break

    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    failed = 0
    success = 0

    broadcast_ids[broadcast_id] = dict(
        total=total_users,
        current=done,
        failed=failed,
        success=success
    )
    async with aiofiles.open('broadcast.txt', 'w') as broadcast_log_file:
        for user in all_users:

            sts, msg = await send_msg(
                user_id=int(user['id']),
                message=response
            )
            if msg is not None:
                await broadcast_log_file.write(msg)

            if sts == 200:
                success += 1
            else:
                failed += 1

            if sts == 400:
                await db.del_user(user['id'])

            done += 1
            if broadcast_ids.get(broadcast_id) is None:
                break
            else:
                broadcast_ids[broadcast_id].update(
                    dict(
                        current=done,
                        failed=failed,
                        success=success
                    )
                )
    if broadcast_ids.get(broadcast_id):
        broadcast_ids.pop(broadcast_id)
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))

    await asyncio.sleep(3)

    if failed == 0:
        await message.reply_text(
            text=f"Broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed."
        )
    else:
        await message.reply_document(
            document='broadcast.txt',
            caption=f"Broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed."
        )

    await aiofiles.os.remove('broadcast.txt')