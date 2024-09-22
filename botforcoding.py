import os
import json
import time
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackContext, CallbackQueryHandler
import autopep8
import pylint.lint
from io import StringIO
from tempfile import NamedTemporaryFile
from typing import Dict

class CodeStorage:
    def __init__(self, storage_file: str = "codes.json"):
        self.storage_file = storage_file
        self.codes: Dict[str, Dict[str, str]] = self._load_codes()

    def _load_codes(self) -> Dict[str, Dict[str, str]]:
        if os.path.exists(self.storage_file):
            with open(self.storage_file, "r") as file:
                return json.load(file)
        return {}

    def save_code(self, user_id: str, code_name: str, code: str) -> None:
        if user_id not in self.codes:
            self.codes[user_id] = {}
        self.codes[user_id][code_name] = code
        self._save()

    def get_codes(self, user_id: str) -> Dict[str, str]:
        return self.codes.get(user_id, {})

    def delete_codes(self, user_id: str) -> None:
        if user_id in self.codes:
            del self.codes[user_id]
        self._save()

    def edit_code(self, user_id: str, code_name: str, new_code: str) -> None:
        if user_id in self.codes and code_name in self.codes[user_id]:
            self.codes[user_id][code_name] = new_code
        self._save()

    def _save(self) -> None:
        with open(self.storage_file, "w") as file:
            json.dump(self.codes, file, indent=4)


class PythonBot:
    def __init__(self, token: str):
        self.updater = Updater(token, use_context=True)
        self.storage = CodeStorage()

        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("my_codes", self.my_codes))
        dp.add_handler(CommandHandler("delete_codes", self.delete_codes))
        dp.add_handler(CommandHandler("edit_code", self.edit_code))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_code))
        dp.add_handler(CallbackQueryHandler(self.handle_button_click))

    def start(self, update: Update, context: CallbackContext) -> None:
        keyboard = [
            [InlineKeyboardButton("تشغيل كود بايثون", callback_data='run_code')],
            [InlineKeyboardButton("تنسيق الكود", callback_data='format_code')],
            [InlineKeyboardButton("تحليل الكود", callback_data='lint_code')],
            [InlineKeyboardButton("أكواد المحفوظة", callback_data='my_codes')],
            [InlineKeyboardButton("تحرير الأكواد", callback_data='edit_code')],
            [InlineKeyboardButton("حذف الأكواد", callback_data='delete_codes')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        developer_name = '<a href="https://t.me/oliceer">OliVer</a>'
        update.message.reply_text(
            f"مرحبًا بك في بوت تحليل وتشغيل الأكواد!\n"
            f"تم تطوير هذا البوت بواسطة: {developer_name}\n"
            f"اختر ما تريد القيام به من الأزرار أدناه:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    def handle_button_click(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()

        context.user_data['callback_data'] = query.data

        if query.data == 'run_code':
            query.edit_message_text("أرسل الكود الذي ترغب في تشغيله.")
        elif query.data == 'format_code':
            query.edit_message_text("أرسل الكود الذي ترغب في تنسيقه.")
        elif query.data == 'lint_code':
            query.edit_message_text("أرسل الكود الذي ترغب في تحليله.")
        elif query.data == 'my_codes':
            self.my_codes(query, context)
        elif query.data == 'edit_code':
            query.edit_message_text("أرسل اسم الكود لتعديله.")
        elif query.data == 'delete_codes':
            self.delete_codes(query, context)

    def handle_code(self, update: Update, context: CallbackContext) -> None:
        user_id = str(update.message.from_user.id)
        code = update.message.text
        callback_data = context.user_data.get('callback_data')

        start_time = time.time()

        if callback_data == 'run_code':
            result = self.execute_code_locally(code)
            duration = time.time() - start_time
            update.message.reply_text(
                f"نتيجة التنفيذ:\n<pre><code>{result}</code></pre>\n"
                f"الوقت المستغرق: {duration:.2f} ثواني",
                parse_mode='HTML'
            )
        elif callback_data == 'format_code':
            formatted_code = self.format_code(code)
            update.message.reply_text(f"الكود بعد التنسيق:\n<pre><code>{formatted_code}</code></pre>", parse_mode='HTML')
        elif callback_data == 'lint_code':
            lint_result = self.lint_code(code)
            update.message.reply_text(
                f"نتائج التحليل:\n<pre><code>{lint_result}</code></pre>",
                parse_mode='HTML'
            )

        code_name = f"code_{len(self.storage.get_codes(user_id)) + 1}"
        self.storage.save_code(user_id, code_name, code)

    def execute_code_locally(self, code: str) -> str:
        try:
            result = subprocess.run(
                ['python3', '-c', code],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"حدث خطأ أثناء التنفيذ: {str(e)}"

    def my_codes(self, update: Update, context: CallbackContext) -> None:
        user_id = str(update.message.from_user.id)
        codes = self.storage.get_codes(user_id)
        if not codes:
            update.message.reply_text("لم تقم بحفظ أي أكواد بعد.")
        else:
            response = "أكوادك المحفوظة:\n"
            for code_name, code in codes.items():
                response += f"<b>{code_name}:</b>\n<pre><code>{code}</code></pre>\n"
            update.message.reply_text(response, parse_mode='HTML')

    def delete_codes(self, update: Update, context: CallbackContext) -> None:
        user_id = str(update.message.from_user.id)
        self.storage.delete_codes(user_id)
        update.message.reply_text("تم حذف جميع الأكواد المحفوظة.")

    def edit_code(self, update: Update, context: CallbackContext) -> None:
        user_id = str(update.message.from_user.id)
        code_name = context.user_data.get('edit_code_name')

        if not code_name:
            code_name = update.message.text.strip()
            codes = self.storage.get_codes(user_id)

            if code_name in codes:
                update.message.reply_text(f"أرسل الكود الجديد ليحل محل {code_name}.")
                context.user_data['edit_code_name'] = code_name
            else:
                update.message.reply_text(f"لم يتم العثور على كود باسم {code_name}.")
        else:
            new_code = update.message.text
            self.storage.edit_code(user_id, code_name, new_code)
            update.message.reply_text(f"تم تعديل الكود {code_name} بنجاح.")
            del context.user_data['edit_code_name']

    def format_code(self, code: str) -> str:
        try:
            formatted_code = autopep8.fix_code(code)
            return formatted_code
        except Exception as e:
            return f"حدث خطأ أثناء تنسيق الكود: {str(e)}"

    def lint_code(self, code: str) -> str:
        pylint_output = StringIO()
        with NamedTemporaryFile("w+", delete=False) as tmp_file:
            tmp_file.write(code.encode('utf-8'))
            tmp_file.flush()
            pylint.lint.Run([tmp_file.name], stdout=pylint_output)  # إزالة do_exit
        lint_result = pylint_output.getvalue()
        return lint_result

    def run(self) -> None:
        while True:
            try:
                print("Starting the bot...")
                self.updater.start_polling()  # Start the bot
                self.updater.idle()
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}. Exiting.")
                break

if __name__ == "__main__":
    TOKEN = "8119443898:AAFwm5E368v-Ov-M_XGBQYCJxj1vMDQbv-0"  # ضع التوكن الخاص بك هنا
    bot = PythonBot(TOKEN)
    bot.run()