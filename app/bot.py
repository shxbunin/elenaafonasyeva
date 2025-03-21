import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = ""
ADMINS = [645334295, 492210589]
bot = Bot(token=TOKEN)
dp = Dispatcher()
captions = {}

DATA_FILE = os.path.join("static", "d.json")
PHOTOS_DIR = os.path.join("static", "photos")
GALLERIES = ["Галерея I", "Галерея II", "Галерея III", "Галерея IV", "Галерея V"]

def load_data() -> dict:
    """Загружает данные из JSON-файла."""
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data: dict) -> None:
    """Сохраняет данные в JSON-файл."""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def build_gallery_keyboard(command_prefix: str, filename: str = "") -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопками для всех галерей.
    Параметры:
      command_prefix: строка, которая становится префиксом для callback_data (например, "add", "choose", "delete");
      filename: передается для команды "add", чтобы привязать фото.
    """
    builder = InlineKeyboardBuilder()
    for gallery in GALLERIES:
        if command_prefix == "add":
            callback_data = f"{command_prefix}={gallery}={filename}"
        elif command_prefix in ("choose", "delete"):
            callback_data = f"{command_prefix}={gallery}"
        else:
            callback_data = f"{command_prefix}={gallery}"
        builder.row(InlineKeyboardButton(text=gallery, callback_data=callback_data))
    return builder.as_markup()

def check_admin(user_id: int) -> bool:
    return user_id in ADMINS

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not check_admin(message.from_user.id):
        return
    await message.answer(
        "Привет! Отправь мне фото с текстовым описанием, "
        "и я добавлю его на сайт."
    )


@dp.message(Command("delete"))
async def cmd_delete(message: types.Message):
    if not check_admin(message.from_user.id):
        return
    markup = build_gallery_keyboard("choose")
    await message.answer("Выбери галерею, из которой нужно удалить фото", reply_markup=markup)


@dp.message(lambda message: message.photo is not None)
async def handle_photo(message: types.Message):
    if not check_admin(message.from_user.id):
        return
    file = await bot.get_file(message.photo[-1].file_id)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{os.path.basename(file.file_path)}"
    save_path = os.path.join(PHOTOS_DIR, filename)
    await bot.download_file(file.file_path, save_path)
    
    caption = message.caption or " "
    captions[filename] = caption

    markup = build_gallery_keyboard("add", filename)
    await message.answer("Теперь выберите раздел, в который будет добавлено фото", reply_markup=markup)


@dp.callback_query()
async def handle_callbacks(callback: CallbackQuery):
    data = callback.data.split("=")
    action = data[0]

    if action == "add":
        # data = ['add', 'Галерея I', '<filename>']
        gallery, filename = data[1], data[2]
        data_json = load_data()
        data_json.setdefault(gallery, [])
        data_json[gallery].append([filename, captions.get(filename, " ")])
        save_data(data_json)

        await callback.message.answer("Успешно добавлено на сайт!")
        await callback.message.delete()
        await callback.answer()

    elif action == "choose":
        # data = ['choose', 'Галерея I']
        gallery = data[1]
        data_json = load_data()
        images = data_json.get(gallery, [])

        builder = InlineKeyboardBuilder()
        for idx, _ in enumerate(images):
            # Индексация с 0, отображается как "Фото {idx+1}"
            if idx % 2 == 0:
                builder.row(InlineKeyboardButton(text=f"Фото {idx + 1}", callback_data=f"delete={gallery}={idx}"))
            else:
                builder.add(InlineKeyboardButton(text=f"Фото {idx + 1}", callback_data=f"delete={gallery}={idx}"))

        await callback.message.answer("Теперь выбери фото (расположение как на сайте)", reply_markup=builder.as_markup())
        await callback.message.delete()
        await callback.answer()

    elif action == "delete":
        # data = ['delete', 'Галерея I', '<index>']
        gallery, index_str = data[1], data[2]
        data_json = load_data()
        try:
            index = int(index_str)
            if 0 <= index < len(data_json.get(gallery, [])):
                data_json[gallery].pop(index)
                save_data(data_json)
                await callback.message.answer("Успешно удалено с сайта!")
            else:
                await callback.message.answer("Неверный индекс фото.")
        except ValueError:
            await callback.message.answer("Ошибка при удалении фото.")
        await callback.message.delete()
        await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())