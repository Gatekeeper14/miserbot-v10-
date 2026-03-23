require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 Miserbot V20 starting...");

// Command handler
bot.onText(/\/(\w+)/, (msg, match) => {
  const command = match[1];
  const chatId = msg.chat.id;

  console.log(`📩 Command: ${command}`);

  switch (command) {
    case "start":
      bot.sendMessage(chatId, "🔥 Miserbot V20 ONLINE\nSystem initialized.");
      break;

    case "help":
      bot.sendMessage(chatId, "/start\n/help\n/status\n/ping");
      break;

    case "status":
      bot.sendMessage(chatId, "✅ Bot is running smooth.");
      break;

    case "ping":
      bot.sendMessage(chatId, "🏓 Pong!");
      break;

    default:
      bot.sendMessage(chatId, "❌ Unknown command");
  }
});
