import logging
import sqlite3
from contextlib import closing
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
import random

# إعداد الـ Token الخاص بالبوت
API_TOKEN = '8119443898:AAFwm5E368v-Ov-M_XGBQYCJxj1vMDQbv-0'
OWNER_CHAT_ID = '7161132306'

# تفعيل نظام التسجيل لمراقبة الأخطاء
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد قاعدة البيانات
DATABASE_FILE = "user_data.db"

def init_db():
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'العربية',
                balance REAL DEFAULT 0,
                account_number TEXT
            )
        ''')
        conn.commit()



generated_numbers = set()

def generate_account_number():
    while True:
        account_number = ''.join(random.choices('0123456789', k=8))
        if account_number not in generated_numbers:
            generated_numbers.add(account_number)
            return account_number

def save_user_data(user_id, language, balance, account_number):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, language, balance, account_number)
            VALUES (?, ?, ?, ?)
        ''', (user_id, language, balance, account_number))
        conn.commit()

def load_user_data(user_id):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT language, balance, account_number FROM users WHERE user_id = ?', (user_id,))
        data = cursor.fetchone()
    if data:
        return data
    else:
        account_number = generate_account_number()
        save_user_data(user_id, 'العربية', 0, account_number)
        return 'العربية', 0, account_number

def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    language, balance, account_number = load_user_data(user_id)
    
    welcome_message = (
        "🎉 مرحبًا بك في بوت المرح والأموال! 💰\n\n"
        "هنا حيث يجتمع الترفيه والإثارة مع إدارة أموالك.\n"
        "✨ استعد لمغامرات ممتعة وتحديات مثيرة!\n\n"
        "للبدء، استخدم الأمر '/help' لتتعرف على جميع المزايا المتاحة لك.\n"
        "لا تنسَ التحقق من رصيدك وتحديث معلومات حسابك بانتظام!"
    )
    
    context.bot.send_message(chat_id=update.message.chat_id, text=welcome_message)

def suggestion(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    suggestion_text = ' '.join(context.args)

    if suggestion_text:
        context.bot.send_message(chat_id=OWNER_CHAT_ID, text=f"اقتراح من المستخدم {user_id}: {suggestion_text}")
        update.message.reply_text("✅ تم إرسال اقتراحك بنجاح.")
    else:
        update.message.reply_text("❌ يرجى كتابة اقتراحك بعد الأمر.")

def help_command(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("✨ القسم 1: الأوامر الأساسية", callback_data='help_section_1')],
        [InlineKeyboardButton("💰 القسم 2: نظام النقاط", callback_data='help_section_2')],
        [InlineKeyboardButton("🌍 القسم 3: إدارة اللغة", callback_data='help_section_3')],
        [InlineKeyboardButton("🎟️ القسم 4: العضويات", callback_data='help_section_4')],
        [InlineKeyboardButton("🎁 القسم 5: العروض والمكافآت", callback_data='help_section_5')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='help_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        query = update.callback_query
        query.message.reply_text("📚 مرحبًا! اختر قسمًا لعرض الشرح:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    help_texts = {
        'help_section_1': (
            "📜 <b>الأوامر الأساسية:</b>\n"
            "1️⃣ <b>تغيير اللغة:</b> اكتب '<code>تغيير اللغة</code>' لتغيير لغة البوت.\n"
            "2️⃣ <b>مساعدة:</b> اكتب '<code>help</code>' لعرض التعليمات.\n"
            "3️⃣ <b>الإعدادات:</b> اضبط إعداداتك باستخدام '<code>settings</code>'.\n"
            "4️⃣ <b>المعلومات:</b> تعرف على البوت عبر '<code>info</code>'.\n"
            "5️⃣ <b>اقتراحات:</b> شارك اقتراحاتك بكتابة '<code>اقتراح</code>'.\n"
            "6️⃣ <b>التحقق من حالة الحساب:</b> اكتب '<code>حالة</code>' للتحقق من حالة حسابك والمكافآت المحتملة."
        ),
        'help_section_2': (
            "📊 <b>نظام النقاط والمحفظة:</b>\n"
            "1️⃣ <b>رصيدك:</b> اكتب '<code>رصيدي</code>' لعرض رصيدك.\n"
            "2️⃣ <b>إيداع:</b> استخدم '<code>إيداع [المبلغ]</code>' لإضافة الأموال إلى حسابك.\n"
            "3️⃣ <b>سحب:</b> اكتب '<code>سحب [المبلغ]</code>' لسحب الأموال.\n"
            "4️⃣ <b>تحويل:</b> أرسل أموالًا إلى مستخدم آخر باستخدام '<code>تحويل [المبلغ] إلى [المستخدم]</code>'.\n"
            "5️⃣ <b>المكافآت اليومية:</b> احصل على مكافأتك اليومية بكتابة '<code>المكافأة</code>'.\n"
            "6️⃣ <b>مستوى العضوية:</b> تحقق من مستوى عضويتك الحالي باستخدام '<code>العضوية</code>'.\n"
            "7️⃣ <b>سجل المعاملات:</b> اكتب '<code>المعاملات</code>' لعرض تاريخ معاملاتك المالية."
        ),
        'help_section_3': (
            "🌐 <b>قريباً...</b>\n"),
        'help_section_4': (
            "💼 <b>العضويات والاشتراكات:</b>\n"
            "1️⃣ <b>الترقية:</b> اكتب '<code>ترقية [نوع العضوية]</code>' لترقية حسابك.\n"
            "2️⃣ <b>التحقق من العضوية:</b> استخدم '<code>العضوية</code>' للتحقق من مستوى عضويتك الحالي.\n"
            "3️⃣ <b>إلغاء الاشتراك:</b> إذا كنت ترغب في إلغاء الاشتراك، اكتب '<code>إلغاء الاشتراك</code>'."
        ),
        'help_section_5': (
            "🎁 <b>عروض ومكافآت خاصة:</b>\n"
            "1️⃣ <b>العروض:</b> اكتب '<code>العروض</code>' لعرض العروض الحالية المتاحة لك.\n"
            "2️⃣ <b>المكافأة الخاصة:</b> تحقق من وجود مكافأة خاصة بكتابة '<code>مكافأة خاصة</code>'.\n"
            "3️⃣ <b>المسابقات الشهرية:</b> شارك في المسابقات الشهرية باستخدام '<code>مسابقة الشهر</code>'."
        ),
        'bot_info': (
            "ℹ️ <b>بوت لولي الاقتصادي الترفيهي:</b>\n"
            "هذا البوت مصمم لتقديم تجربة ترفيهية مميزة تجمع بين المرح والإدارة المالية.\n"
            "👨‍💻 <b>المطور:</b> <a href='https://t.me/oliceer'>oliceer</a>"
        ),
        'terms_and_privacy': (
            "📜 <b>بنود الخدمة:</b>\n"
            "1️⃣ <b>قبول الشروط:</b> باستخدامك للبوت، توافق على الالتزام بهذه البنود.\n"
            "2️⃣ <b>استخدام الخدمة:</b> يُسمح لك باستخدام البوت لأغراض ترفيهية فقط.\n"
            "🔒 <b>شروط الخصوصية:</b>\n"
            "1️⃣ <b>جمع المعلومات:</b> نقوم بجمع معلومات محدودة لتحسين تجربتك.\n"
            "2️⃣ <b>حماية المعلومات:</b> نتخذ تدابير أمنية لحماية بياناتك."
        )
    }

    reply_markup_help = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data='help_menu')],
        [InlineKeyboardButton("❌ خروج", callback_data='confirm_exit')],
        [InlineKeyboardButton("ℹ️ معلومات عن البوت", callback_data='bot_info')],
        [InlineKeyboardButton("📜 بنود الخدمة", callback_data='terms_and_privacy')]
    ])
    
    if query.data in help_texts:
        query.edit_message_text(text=help_texts[query.data], parse_mode='HTML', reply_markup=reply_markup_help)
    elif query.data == 'help_menu':
        reply_markup_menu = InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 الأوامر الأساسية", callback_data='help_section_1')],
            [InlineKeyboardButton("📊 نظام النقاط والمحفظة", callback_data='help_section_2')],
            [InlineKeyboardButton("🌐 إدارة اللغة", callback_data='help_section_3')],
            [InlineKeyboardButton("💼 العضويات والاشتراكات", callback_data='help_section_4')],
            [InlineKeyboardButton("🎁 عروض ومكافآت خاصة", callback_data='help_section_5')],
            [InlineKeyboardButton("❌ خروج", callback_data='confirm_exit')]
        ])
        query.edit_message_text(text="📚 مرحبًا! اختر قسمًا لعرض الشرح:", reply_markup=reply_markup_menu)
    elif query.data == 'confirm_exit':
        reply_markup_confirm = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ نعم، الخروج", callback_data='exit_help')],
            [InlineKeyboardButton("🔙 لا، العودة", callback_data='help_menu')]
        ])
        query.edit_message_text(text="⚠️ هل أنت متأكد أنك تريد الخروج؟", reply_markup=reply_markup_confirm)
    elif query.data == 'exit_help':
        query.edit_message_text(text="✅ تم الخروج من قائمة المساعدة. إذا كنت بحاجة إلى مساعدة أخرى، اكتب 'help'.", reply_markup=None)

def handle_help(update, context):
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 الأوامر الأساسية", callback_data='help_section_1')],
        [InlineKeyboardButton("📊 نظام النقاط والمحفظة", callback_data='help_section_2')],
        [InlineKeyboardButton("🌐 إدارة اللغة", callback_data='help_section_3')],
        [InlineKeyboardButton("💼 العضويات والاشتراكات", callback_data='help_section_4')],
        [InlineKeyboardButton("🎁 عروض ومكافآت خاصة", callback_data='help_section_5')],
        [InlineKeyboardButton("ℹ️ معلومات عن البوت", callback_data='bot_info')],
        [InlineKeyboardButton("📜 بنود الخدمة", callback_data='terms_and_privacy')],
        [InlineKeyboardButton("❌ خروج", callback_data='confirm_exit')]
    ])
    update.message.reply_text("📚 مرحبًا! اختر قسمًا لعرض الشرح:", reply_markup=reply_markup)
    
# دالة لمعالجة الأوامر المدخلة من المستخدم
def handle_commands(update: Update, context: CallbackContext) -> None:
    command = update.message.text.strip()  # إزالة المسافات الزائدة من نص الأمر
    user_id = update.message.from_user.id  # معرف المستخدم
    language, balance, account_number = load_user_data(user_id)  # تحميل بيانات المستخدم

    try:
        # التعامل مع الأوامر المختلفة
        if command == '/start':
            handle_start(update, context)  # بدء التفاعل
        elif command in ['help', 'help/', '/help', 'مساعدة', 'مساعده']:
            handle_help(update, context)  # عرض المساعدة
        elif command == 'حسابي':
            handle_account_info(update, language, balance, account_number)  # عرض معلومات الحساب
        elif command.startswith('اقتراح'):
            suggestion(update, context)  # استدعاء دالة الاقتراحات
        else:
            update.message.reply_text("❌ الأمر غير معروف. حاول مرة أخرى.")  # رسالة للأوامر غير المعروفة
    except Exception as e:
        update.message.reply_text(f"❌ حدث خطأ أثناء معالجة الأمر: {str(e)}")
def handle_command(update: Update, context: CallbackContext) -> None:
        command = update.message.text.split()[0].lower()  # تحديد الأمر المدخل

        if command == 'اقتراح':
            suggestion(update, context)
  
        elif command == 'تغيير اللغة':
            handle_change_language(update)  # تغيير اللغة
        elif command == 'settings':
            handle_settings(update)  # إعدادات المستخدم
        elif command == 'info':
            handle_info(update)  # معلومات عن البوت
        elif command.startswith('إيداع'):
            handle_deposit(update, command, user_id, language, balance, account_number)  # إيداع الأموال
        elif command.startswith('سحب'):
            handle_withdraw(update, command, user_id, language, balance, account_number)  # سحب الأموال
        elif command.startswith('تحويل'):
            handle_transfer(update, command, user_id, language, balance, account_number)  # تحويل الأموال
        elif command == 'رصيدي':
            handle_balance(update, balance)  # عرض الرصيد
        
    except Exception as e:
        # تسجيل أي أخطاء تظهر
        logger.error(f"Error handling command: {e}")

# دالة لمعالجة عرض المساعدة


def handle_start(update, context):
    handle_message(update, context)

# دالة لمعالجة عرض المساعدة
def handle_help(update, context):
    # نص المساعدة المبدئي
    help_text = (
        "📚 <b>قائمة الأوامر:</b>\n"
        "للحصول على تفاصيل حول أي قسم، اضغط على الزر أدناه."
    )
    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📜 الأوامر الأساسية", callback_data='help_section_1'),
            InlineKeyboardButton("📊 نظام النقاط والمحفظة", callback_data='help_section_2')
        ],
        [
            InlineKeyboardButton("🌐 إدارة اللغة", callback_data='help_section_3'),
            InlineKeyboardButton("💼 العضويات والاشتراكات", callback_data='help_section_4')
        ],
        [
            InlineKeyboardButton("🎁 عروض ومكافآت خاصة", callback_data='help_section_5'),
            InlineKeyboardButton("🔙 إغلاق", callback_data='close_help')
        ]
    ])
    update.message.reply_text(text=help_text, parse_mode='HTML', reply_markup=reply_markup)
def handle_account_info(update, language, balance, account_number):
    update.message.reply_text(f"📊 معلومات حسابك:\n- اللغة: {language}\n- الرصيد: {balance}\n- رقم الحساب: {account_number}")

def handle_change_language(update):
    update.message.reply_text("⚙️ يرجى تحديد اللغة الجديدة.")

def handle_settings(update):
    update.message.reply_text("🛠️ هنا يمكنك ضبط إعداداتك.")

def handle_info(update):
    

# نص بنود الخدمة
terms_text = (
    "📜 <b>بنود الخدمة:</b>\n"
    "1️⃣ <b>قبول الشروط:</b> باستخدامك للبوت، توافق على الالتزام بهذه البنود. إذا كنت لا توافق، يُرجى عدم استخدام البوت. تعتبر هذه الشروط سارية المفعول عند بدء استخدامك للخدمة.\n\n"
    
    "2️⃣ <b>استخدام الخدمة:</b> يُسمح لك باستخدام البوت لأغراض ترفيهية فقط. أي استخدام تجاري أو غير قانوني ممنوع، ويحق لنا اتخاذ إجراءات قانونية ضد أي انتهاك.\n\n"
    
    "3️⃣ <b>حماية البيانات:</b> نحن نأخذ خصوصيتك على محمل الجد ونتعهد بحماية معلوماتك الشخصية. نقوم بتطبيق تدابير أمنية متقدمة لمنع أي تسرب أو استخدام غير مصرح به لمعلوماتك.\n\n"
    
    "4️⃣ <b>التعديلات:</b> نحتفظ بالحق في تعديل هذه البنود في أي وقت دون إشعار مسبق. يُنصح بمراجعة هذه البنود بانتظام لضمان عدم تفويت أي تغييرات مهمة.\n\n"
    
    "5️⃣ <b>إخلاء المسؤولية:</b> البوت لا يتحمل أي مسؤولية عن الأضرار الناتجة عن استخدامه، بما في ذلك الأضرار المباشرة وغير المباشرة. يجب عليك استخدام البوت على مسؤوليتك الخاصة.\n\n"
    
    "6️⃣ <b>التواصل:</b> إذا كان لديك أي استفسارات أو مخاوف بشأن هذه البنود، يمكنك التواصل معنا عبر المطور. نحن هنا لمساعدتك واستقبال آرائك.\n"
)

# نص شروط الخصوصية
privacy_text = (
    "🔒 <b>شروط الخصوصية:</b>\n"
    "1️⃣ <b>جمع المعلومات:</b> نقوم بجمع معلومات محدودة لتحسين تجربتك، مثل معلومات الاستخدام وبيانات الجهاز. هذه المعلومات تساعدنا في تحسين خدماتنا باستمرار.\n\n"
    
    "2️⃣ <b>استخدام المعلومات:</b> تُستخدم المعلومات لتحسين الخدمة وتقديم دعم مخصص والتواصل معك بشأن التحديثات والمميزات الجديدة. نحن نضمن عدم استخدام معلوماتك لأغراض غير متعلقة بالخدمة.\n\n"
    
    "3️⃣ <b>حماية المعلومات:</b> نتخذ تدابير أمنية لحماية بياناتك، بما في ذلك تشفير المعلومات والتأكد من عدم الوصول غير المصرح به. نعمل بجد لضمان أمان بياناتك في جميع الأوقات.\n\n"
    
    "4️⃣ <b>مشاركة المعلومات:</b> لن نشارك معلوماتك مع أطراف ثالثة دون موافقتك، إلا إذا كان ذلك مطلوبًا بموجب القانون. نحن نحترم خصوصيتك ونتعامل مع بياناتك بأقصى درجات الأمان.\n\n"
    
    "5️⃣ <b>حقوقك:</b> لديك الحق في الوصول إلى معلوماتك الشخصية وطلب تصحيحها أو حذفها. يمكنك ممارسة هذه الحقوق عن طريق التواصل معنا عبر المطور. نحن هنا لضمان حقوقك.\n\n"
    
    "6️⃣ <b>تغييرات في سياسة الخصوصية:</b> قد نقوم بتحديث سياسة الخصوصية هذه من وقت لآخر. سيتم إخطارك بأي تغييرات جوهرية، لذا يُفضل مراجعة السياسة بشكل دوري.\n"
)

# معلومات عن البوت
update.message.reply_text(
    "ℹ️ <b>معلومات عن بوت لولي الاقتصادي الترفيهي:</b>\n"
    "هذا البوت مصمم لتقديم تجربة ترفيهية مميزة تجمع بين المرح والإدارة المالية.\n"
    "استمتع باللعب والدردشة، واستكشاف ميزات ممتعة تساعدك في قضاء وقت رائع.\n\n"
    "👨‍💻 <b>المطور:</b> \n"
    "<a href='https://t.me/oliceer'>oliceer</a>",
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 بنود الخدمة", callback_data='terms')],
        [InlineKeyboardButton("🔒 سياسة الخصوصية", callback_data='privacy')]
    ]),
    parse_mode='HTML'
)

# التعامل مع الأزرار
def button(update, context):
    query = update.callback_query
    if query.data == 'terms':
        query.edit_message_text(text=terms_text, parse_mode='HTML')
    elif query.data == 'privacy':
        query.edit_message_text(text=privacy_text, parse_mode='HTML')

def handle_deposit(update, command, user_id, language, balance, account_number):
    try:
        amount = float(command.split()[1])
        if amount > 0:
            balance += amount
            save_user_data(user_id, language, balance, account_number)
            update.message.reply_text(f"💵 تم إيداع <b>{amount}</b> بنجاح. رصيدك الجديد هو <b>{balance}</b>.", parse_mode='HTML')
        else:
            update.message.reply_text(
    "❌ <b>خطأ:</b> يجب أن يكون المبلغ أكبر من صفر.",
    parse_mode='HTML')
    except (ValueError, IndexError):
        update.message.reply_text(
    "❌ <b>خطأ:</b> صيغة الأمر غير صحيحة.\n"
    "يجب عليك كتابة الأمر كالتالي:\n"
    "<b>إيداع \"المبلغ\"</b>\n"
    "مثال: <code>إيداع 100</code> لإضافة 100 وحدة.",
    parse_mode='HTML')

def handle_withdraw(update, command, user_id, language, balance, account_number):
    try:
        amount = float(command.split()[1])
        if amount <= balance:
            balance -= amount
            save_user_data(user_id, language, balance, account_number)
            update.message.reply_text(f"💸 تم سحب <b>{amount}</b> بنجاح. رصيدك الجديد هو <b>{balance}</b>.", parse_mode='HTML')
        else:
            update.message.reply_text(
    "❌ <b>خطأ:</b> رصيدك غير كافٍ لإجراء هذه العملية.",
    parse_mode='HTML')
    except (ValueError, IndexError):
    update.message.reply_text(
        "❌ <b>خطأ:</b> صيغة الأمر غير صحيحة.\n"
        "اكتب الأمر كالتالي:\n"
        "<b>سحب \"المبلغ\"</b>\n"
        "مثال: <code>سحب 100</code> لسحب 100 وحدة.",
        parse_mode='HTML')

def handle_transfer(update, command, user_id, language, balance, account_number):
    try:
        parts = command.split()
        amount = float(parts[1])
        recipient = int(parts[3])
        recipient_data = load_user_data(recipient)
        if recipient_data:
            recipient_balance = recipient_data[1]
            if amount <= balance:
                balance -= amount
                recipient_balance += amount
                save_user_data(user_id, language, balance, account_number)
                save_user_data(recipient, recipient_data[0], recipient_balance, recipient_data[2])
                update.message.reply_text(f"➡️ تم تحويل <b>{amount}</b> إلى <b>{recipient}</b> بنجاح.", parse_mode='HTML')
            else:
                update.message.reply_text("❌ رصيدك غير كافٍ لإجراء هذه العملية.")
        else:
            update.message.reply_text("❓ لم يتم العثور على المستخدم الذي تحاول التحويل إليه.")
    except (ValueError, IndexError):
        update.message.reply_text("❌ صيغة الأمر غير صحيحة. يجب أن تكتب: تحويل [المبلغ] إلى [معرف المستلم].")

def handle_balance(update, balance):
    update.message.reply_text(f"💰 رصيدك الحالي هو: <b>{balance}</b>.", parse_mode='HTML')