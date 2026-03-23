require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 Miserbot V24 starting...");

// =======================
// COMMAND HANDLER
// =======================

async function handleCommand(chatId, command) {

  switch(command) {

    case "start":
      bot.sendMessage(chatId, "🔥 Miserbot V24\nSystem rebooted.\nChoose an option:", {
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
      const start = Date.now();
      const msg = await bot.sendMessage(chatId, "🏓 Pinging...");
      const end = Date.now();
      bot.editMessageText(`🏓 Pong!\n${end - start}ms`, {
        chat_id: chatId,
        message_id: msg.message_id
      });
      break;

    case "tools":
      bot.sendMessage(chatId, "🧰 Choose a tool:", {
        reply_markup: {
          keyboard: [
            ["💰 BTC Price", "💎 ETH Price"],
            ["⬅️ Back"]
          ],
          resize_keyboard: true
        }
      });
      break;

    case "btc":
      try {
        const res = await axios.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json");
        const price = res.data.bpi.USD.rate;
        bot.sendMessage(chatId, `₿ BTC Price: $${price}`);
      } catch (err) {
        bot.sendMessage(chatId, "Error fetching BTC price.");
      }
      break;

    case "eth":
      try {
        bot.sendMessage(chatId, "ETH coming soon...");
      } catch (err) {
        bot.sendMessage(chatId, "Error fetching ETH.");
      }
      break;

    case "back":
      handleCommand(chatId, "start");
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

  if (text === "💰 BTC Price") handleCommand(chatId, "btc");
  if (text === "💎 ETH Price") handleCommand(chatId, "eth");
  if (text === "⬅️ Back") handleCommand(chatId, "back");
});
