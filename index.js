require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 Miserbot V22 starting...");

// =======================
// COMMAND + BUTTON HANDLER
// =======================

function handleCommand(chatId, command) {

  switch(command) {

    case "start":
      bot.sendMessage(chatId, "🔥 Miserbot V22\nChoose an option:", {
        reply_markup: {
          keyboard: [
            ["🚀 Start", "📊 Status"],
            ["🧰 Tools", "❓ Help"]
          ],
          resize_keyboard: true
        }
      });
      break;

    case "help":
      bot.sendMessage(chatId, "Commands:\n/start\n/help\n/status\n/ping");
      break;

    case "status":
      bot.sendMessage(chatId, "✅ Bot running smoothly.");
      break;

    case "ping":
      bot.sendMessage(chatId, "🏓 Pong!");
      break;

    case "tools":
      bot.sendMessage(chatId, "🧰 Tools coming soon...");
      break;

    default:
      bot.sendMessage(chatId, "Unknown command.");
  }
}

// =======================
// COMMAND LISTENER
// =======================

bot.onText(/\/(.+)/, (msg, match) => {
  const chatId = msg.chat.id;
  const command = match[1];

  handleCommand(chatId, command);
});

// =======================
// BUTTON LISTENER
// =======================

bot.on("message", (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  if (!text) return;

  if (text === "🚀 Start") handleCommand(chatId, "start");
  if (text === "📊 Status") handleCommand(chatId, "status");
  if (text === "🧰 Tools") handleCommand(chatId, "tools");
  if (text === "❓ Help") handleCommand(chatId, "help");
});
