const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");

// ===== TOKEN =====
const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, { polling: true });

// ===== STORAGE =====
let userAlerts = {}; // { chatId: { target: number, triggered: false } }

// ===== GET BTC PRICE (PRO) =====
async function getBTCPrice() {
  try {
    const res = await axios.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT");
    return parseFloat(res.data.price);
  } catch {
    try {
      const res = await axios.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json");
      return parseFloat(res.data.bpi.USD.rate.replace(/,/g, ""));
    } catch (err) {
      console.log("BTC API FAILED:", err.message);
      return null;
    }
  }
}

// ===== START =====
bot.onText(/\/start/, (msg) => {
  bot.sendMessage(msg.chat.id, "🔥 Miserbot PRO Ready\n\nCommands:\n• BTC Price\n• Set Alert\n• My ID\n• Status");
});

// ===== BTC PRICE =====
bot.onText(/BTC Price/i, async (msg) => {
  const chatId = msg.chat.id;
  const price = await getBTCPrice();

  if (!price) {
    bot.sendMessage(chatId, "❌ Failed to fetch BTC price");
    return;
  }

  bot.sendMessage(chatId, `💰 BTC: $${price}`);
});

// ===== SET ALERT =====
bot.onText(/Set Alert/i, (msg) => {
  bot.sendMessage(msg.chat.id, "💬 Send BTC price (example: 72000)");
});

bot.on("message", async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  // Ignore commands
  if (!text || text.startsWith("/")) return;

  // If it's a number → set alert
  if (!isNaN(text)) {
    userAlerts[chatId] = {
      target: parseFloat(text),
      triggered: false
    };

    bot.sendMessage(chatId, `🔔 Alert set for BTC ABOVE $${text}`);
  }
});

// ===== STATUS =====
bot.onText(/Status/i, (msg) => {
  bot.sendMessage(msg.chat.id, "✅ Bot running");
});

// ===== CHAT ID =====
bot.onText(/My ID/i, (msg) => {
  bot.sendMessage(msg.chat.id, `🆔 Your Chat ID: ${msg.chat.id}`);
});

// ===== SMART ALERT ENGINE =====
setInterval(async () => {
  const price = await getBTCPrice();
  if (!price) return;

  for (let chatId in userAlerts) {
    const alert = userAlerts[chatId];

    if (!alert.triggered && price >= alert.target) {
      bot.sendMessage(chatId, `🚨 BTC HIT TARGET!\n💰 Price: $${price}`);
      alert.triggered = true; // prevent spam
    }

    // Reset if price drops again (optional smart behavior)
    if (alert.triggered && price < alert.target - 500) {
      alert.triggered = false;
    }
  }

}, 10000); // every 10 sec

console.log("🚀 Miserbot PRO running...");
