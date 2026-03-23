require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 Miserbot V23 starting...");

// =======================
// COMMAND HANDLER
// =======================

async function handleCommand(chatId, command) {

  switch(command) {

    case "start":
      bot.sendMessage(chatId, "🔥 Miserbot V23\nChoose an option:", {
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
        const res = await axios.get("https://api.coindesk.com/v1/bpi/currentprice/ETH.json");
        const price = res.data.bpi.USD.rate;
        bot.sendMessage(chatId, `💎 ETH Price: $${price}`);
      } catch (err) {
        bot.sendMessage(chatId, "Error fetching ETH price.");
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
