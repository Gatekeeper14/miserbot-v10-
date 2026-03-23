require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 Miserbot V21 starting...");

// START COMMAND WITH BUTTONS
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;

  bot.sendMessage(chatId, "🔥 Miserbot V21\nChoose an option:", {
    reply_markup: {
      keyboard: [
        ["🚀 Start", "📊 Status"],
        ["🧰 Tools", "❓ Help"]
      ],
      resize_keyboard: true
    }
  });
});

// BUTTON HANDLER
bot.on("message", (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  if (!text) return;

  if (text === "🚀 Start") {
    bot.sendMessage(chatId, "System initialized.");
  } 
  else if (text === "📊 Status") {
    bot.sendMessage(chatId, "✅ Bot running smoothly.");
  } 
  else if (text === "🧰 Tools") {
    bot.sendMessage(chatId, "Tools coming soon...");
  } 
  else if (text === "❓ Help") {
    bot.sendMessage(chatId, "Use the buttons to navigate.");
  }
});
