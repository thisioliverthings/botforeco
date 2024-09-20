import org.telegram.telegrambots.bots.TelegramLongPollingBot;
import org.telegram.telegrambots.meta.api.methods.send.SendMessage;
import org.telegram.telegrambots.meta.api.objects.Update;
import org.telegram.telegrambots.meta.exceptions.TelegramApiException;

import java.sql.*;
import java.util.HashSet;
import java.util.Random;

public class MyTelegramBot extends TelegramLongPollingBot {
    private static final String API_TOKEN = "8119443898:AAFwm5E368v-Ov-M_XGBQYCJxj1vMDQbv-0";
    private static final String OWNER_CHAT_ID = "7161132306";
    private static final String DATABASE_URL = "jdbc:sqlite:user_data.db";
    private static final HashSet<String> generatedNumbers = new HashSet<>();

    public MyTelegramBot() {
        initDb();
    }

    private void initDb() {
        try (Connection conn = DriverManager.getConnection(DATABASE_URL);
             Statement stmt = conn.createStatement()) {
            stmt.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, language TEXT DEFAULT 'العربية', balance REAL DEFAULT 0, account_number TEXT)");
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private String generateAccountNumber() {
        Random random = new Random();
        String accountNumber;
        do {
            accountNumber = String.valueOf(random.nextInt(100000000));
        } while (generatedNumbers.contains(accountNumber));
        generatedNumbers.add(accountNumber);
        return accountNumber;
    }

    private void saveUserData(long userId, String language, double balance, String accountNumber) {
        String sql = "INSERT OR REPLACE INTO users (user_id, language, balance, account_number) VALUES (?, ?, ?, ?)";
        try (Connection conn = DriverManager.getConnection(DATABASE_URL);
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setLong(1, userId);
            pstmt.setString(2, language);
            pstmt.setDouble(3, balance);
            pstmt.setString(4, accountNumber);
            pstmt.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private String[] loadUserData(long userId) {
        String sql = "SELECT language, balance, account_number FROM users WHERE user_id = ?";
        try (Connection conn = DriverManager.getConnection(DATABASE_URL);
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setLong(1, userId);
            ResultSet rs = pstmt.executeQuery();
            if (rs.next()) {
                return new String[]{rs.getString("language"), String.valueOf(rs.getDouble("balance")), rs.getString("account_number")};
            } else {
                String accountNumber = generateAccountNumber();
                saveUserData(userId, "العربية", 0, accountNumber);
                return new String[]{"العربية", "0.0", accountNumber};
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return null;
    }

    @Override
    public void onUpdateReceived(Update update) {
        if (update.hasMessage() && update.getMessage().hasText()) {
            handleCommand(update);
        }
    }

    private void handleCommand(Update update) {
        String command = update.getMessage().getText().trim();
        long userId = update.getMessage().getFrom().getId();
        String[] userData = loadUserData(userId);
        String language = userData[0];
        double balance = Double.parseDouble(userData[1]);
        String accountNumber = userData[2];

        switch (command) {
            case "/start":
                handleStart(update);
                break;
            case "اقتراح":
                // Handle suggestion logic here
                break;
            case "حسابي":
                handleAccountInfo(update, language, balance, accountNumber);
                break;
            case "help":
                // Handle help logic here
                break;
            default:
                sendMessage(update.getMessage().getChatId(), "❌ الأمر غير معروف. حاول مرة أخرى.");
                break;
        }
    }

    private void handleStart(Update update) {
        String welcomeMessage = "🎉 مرحبًا بك في بوت المرح والأموال! 💰\n" +
                "هنا حيث يجتمع الترفيه والإثارة مع إدارة أموالك.\n" +
                "✨ استعد لمغامرات ممتعة وتحديات مثيرة!\n" +
                "للبدء، استخدم الأمر '/help' لتتعرف على جميع المزايا المتاحة لك.";
        sendMessage(update.getMessage().getChatId(), welcomeMessage);
    }

    private void handleAccountInfo(Update update, String language, double balance, String accountNumber) {
        String infoMessage = String.format("📊 معلومات حسابك:\n- اللغة: %s\n- الرصيد: %.2f\n- رقم الحساب: %s", language, balance, accountNumber);
        sendMessage(update.getMessage().getChatId(), infoMessage);
    }

    private void sendMessage(Long chatId, String text) {
        SendMessage message = new SendMessage();
        message.setChatId(String.valueOf(chatId));
        message.setText(text);
        try {
            execute(message);
        } catch (TelegramApiException e) {
            e.printStackTrace();
        }
    }

    @Override
    public String getBotUsername() {
        return "@eco_js_bot";
    }

    @Override
    public String getBotToken() {
        return API_TOKEN;
    }
}