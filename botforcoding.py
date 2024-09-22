import os
import docker
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackContext, CallbackQueryHandler
import autopep8
import pylint.lint
from io import StringIO
from tempfile import NamedTemporaryFile
from typing import Dict, Any

# Enhanced JSON storage with edit and reset functionality
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


# Advanced bot class with performance monitoring, AI suggestions, and enhanced UI
class PythonBot:
    def __init__(self, token: str):
        self.updater = Updater(token, use_context=True)
        self.storage = CodeStorage()
        self.docker_client = docker.from_env()

        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("my_codes", self.my_codes))
        dp.add_handler(CommandHandler("delete_codes", self.delete_codes))
        dp.add_handler(CommandHandler("edit_code", self.edit_code))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_code))
        dp.add_handler(CallbackQueryHandler(self.handle_button_click))

    # Start function with enhanced buttons and developer name as a clickable HTML link
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
    
    # Developer name with HTML link
        developer_name = '<a href="https://t.me/oliceer">OliVer</a>'
    
    # Welcome message with developer name as a clickable HTML link
        update.message.reply_text(
            f"مرحبًا بك في بوت تحليل وتشغيل الأكواد!\n"
            f"تم تطوير هذا البوت بواسطة: {developer_name}\n"
            f"اختر ما تريد القيام به من الأزرار أدناه:",
            reply_markup=reply_markup,
            parse_mode='HTML'  # Use HTML parse mode for links
        ) 
    # Handle button clicks
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

    # Handle code sent by the user with performance monitoring
    def handle_code(self, update: Update, context: CallbackContext) -> None:
        user_id = str(update.message.from_user.id)
        code = update.message.text
        callback_data = context.user_data.get('callback_data')

        start_time = time.time()

        if callback_data == 'run_code':
            result = self.execute_code_in_docker(code)
            duration = time.time() - start_time
            update.message.reply_text(f"نتيجة التنفيذ:\n```{result}```\nالوقت المستغرق: {duration:.2f} ثواني", parse_mode='Markdown')

        elif callback_data == 'format_code':
            formatted_code = self.format_code(code)
            update.message.reply_text(f"الكود بعد التنسيق:\n```{formatted_code}```", parse_mode='Markdown')

        elif callback_data == 'lint_code':
            lint_result = self.lint_code(code)
            ai_suggestions = self.provide_ai_suggestions(lint_result)
            update.message.reply_text(f"نتائج التحليل:\n```{lint_result}```\nاقتراحات الذكاء الاصطناعي:\n{ai_suggestions}", parse_mode='Markdown')

        # Save code in all cases
        code_name = f"code_{len(self.storage.get_codes(user_id)) + 1}"
        self.storage.save_code(user_id, code_name, code)

    # Run code in Docker with advanced security measures
    def execute_code_in_docker(self, code: str) -> str:
        try:
            container = self.docker_client.containers.run(
                "python:3.8-slim",
                f"python -c \"{code}\"",
                remove=True,
                stdout=True,
                stderr=True,
                mem_limit="50m",
                cpu_period=100000,
                cpu_quota=50000,
                network_disabled=True,  # Disable network for security
                security_opt=["no-new-privileges"],  # Additional security
            )
            return container.decode("utf-8")
        except Exception as e:
            return f"حدث خطأ أثناء التنفيذ: {str(e)}"

    # Return user's saved codes
    def my_codes(self, update: Update, context: CallbackContext) -> None:
        user_id = str(update.message.from_user.id)
        codes = self.storage.get_codes(user_id)
        if not codes:
            update.message.reply_text("لم تقم بحفظ أي أكواد بعد.")
        else:
            response = "أكوادك المحفوظة:\n"
            for code_name, code in codes.items():
                response += f"{code_name}:\n```{code}```\n\n"
            update.message.reply_text(response, parse_mode='Markdown')

    # Delete user's saved codes
    def delete_codes(self, update: Update, context: CallbackContext) -> None:
        user_id = str(update.message.from_user.id)
        self.storage.delete_codes(user_id)
        update.message.reply_text("تم حذف جميع الأكواد المحفوظة.")

    # Edit a saved code
    def edit_code(self, update: Update, context: CallbackContext) -> None:
        user_id = str(update.message.from_user.id)
        code_name = update.message.text.strip()
        codes = self.storage.get_codes(user_id)

        if code_name in codes:
            update.message.reply_text(f"أرسل الكود الجديد ليحل محل {code_name}.")
            context.user_data['edit_code_name'] = code_name
        else:
            update.message.reply_text(f"لم يتم العثور على كود باسم {code_name}.")

# Provide AI suggestions based on linting errors
    def provide_ai_suggestions(self, lint_output: str) -> str:
        suggestions = []
        
        if "indentation" in lint_output:
            suggestions.append("تحقق من استخدام المسافات بشكل صحيح لتنظيم الكود.")
        if "unused-variable" in lint_output:
            suggestions.append("قم بإزالة المتغيرات غير المستخدمة لتحسين الكود.")
        if "missing-docstring" in lint_output:
            suggestions.append("أضف توثيقات (docstrings) إلى وظائفك لتوضيح الغرض منها.")
        if "too-many-branches" in lint_output:
            suggestions.append("قد يكون لديك عدد كبير من التفرعات (if-else). حاول تقليل التعقيد باستخدام استراتيجيات مثل التجريد.")
        if "too-many-arguments" in lint_output:
            suggestions.append("وظيفتك تحتوي على عدد كبير من المعاملات. حاول تقليلها من خلال تقسيم الكود إلى وظائف أصغر.")
        if "line-too-long" in lint_output:
            suggestions.append("بعض الأسطر طويلة جدًا. حاول تقسيمها لتصبح أكثر قابلية للقراءة.")
        
        if not suggestions:
            return "الكود يبدو جيدًا ولا توجد اقتراحات كبيرة."
        
        return "\n".join(suggestions)

    # Handle editing of existing codes with confirmation
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

    # Format code using autopep8
    def format_code(self, code: str) -> str:
        try:
            formatted_code = autopep8.fix_code(code)
            return formatted_code
        except Exception as e:
            return f"حدث خطأ أثناء تنسيق الكود: {str(e)}"

    # Lint code using pylint with AI suggestions
    def lint_code(self, code: str) -> str:
        pylint_output = StringIO()
        with NamedTemporaryFile("w+", delete=False) as tmp_file:
            tmp_file.write(code)
            tmp_file.flush()
            pylint.lint.Run([tmp_file.name], do_exit=False, stdout=pylint_output)
        lint_result = pylint_output.getvalue()
        ai_suggestions = self.provide_ai_suggestions(lint_result)
        return f"{lint_result}\n\nاقتراحات الذكاء الاصطناعي:\n{ai_suggestions}"

    # Start the bot
    def run(self) -> None:
        self.updater.start_polling()
        self.updater.idle()


# Run the bot
if __name__ == "__main__":
    TOKEN = "8119443898:AAFwm5E368v-Ov-M_XGBQYCJxj1vMDQbv-0"  # ضع التوكن الخاص بك هنا
    bot = PythonBot(TOKEN)
    bot.run()