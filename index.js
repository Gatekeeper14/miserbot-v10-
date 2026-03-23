const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");
const fs = require("fs");

// ===== SAFE START =====
if (!process.env.TELEGRAM_BOT_TOKEN) {
  console.error("❌ TELEGRAM_BOT_TOKEN missing!");
  process.exit(1);
}

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, {
  polling: true,
});

// ===== STORAGE =====
let userAlerts = {};
let cooldown = {}; // anti-spam

function loadData() {
  try {
    userAlerts = JSON.parse(fs.readFileSync("alerts.json"));
  } catch {
    userAlerts = {};
  }
}

function saveData() {
  fs.writeFileSync("alerts.json", JSON.stringify(userAlerts, null, 2));
}

loadData();

// ===== BTC PRICE (3 SOURCES) =====
async function getBTCPrice() {
  // Binance
  try {
    const r = await axios.get(
      "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
      { timeout: 4000 }
    );
    return parseFloat(r.data.price);
  } catch {}

  // Coinbase
  try {
    const r = await axios.get(
      "https://api.coinbase.com/v2/prices/BTC-USD/spot",
      { timeout: 4000 }
    );
    return parseFloat(r.data.data.amount);
  } catch {}

  // Coingecko
  try {
    const r = await axios.get(
      "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
      { timeout: 4000 }
    );
    return r.data.bitcoin.usd;
  } catch {}

  return null;
}

// ===== SAFE SEND (ANTI-SPAM + NO CRASH) =====
async function safeSend(chatId, text) {
  try {
    if (cooldown[chatId] && Date.now() - cooldown[chatId] < 1000) return;
    cooldown[chatId] = Date.now();

    await bot.sendMessage(chatId, text);
  } catch (err) {
    console.log("Send error:", err.message);
  }
}

// ===== COMMANDS =====

// START
bot.onText(/\/start/, (msg) => {
  safeSend(msg.chat.id, "🔥 Miserbot V35 Online");
  safeSend(msg.chat.id, "💬 Send BTC price (example: 70000)");
});

// STATUS
bot.onText(/status/i, (msg) => {
  safeSend(msg.chat.id, "✅ Bot running stable");
});

// BTC PRICE
bot.onText(/btc price/i, async (msg) => {
  const price = await getBTCPrice();

  if (!price) {
    safeSend(msg.chat.id, "❌ All price sources failed");
    return;
  }

  safeSend(msg.chat.id, `💰 BTC: $${price}`);
});

// CHAT ID
bot.onText(/my id/i, (msg) => {
  safeSend(msg.chat.id, `🆔 ID: ${msg.chat.id}`);
});

// HELP
bot.onText(/help/i, (msg) => {
  safeSend(
    msg.chat.id,
    "📘 Commands:\n💰 BTC Price\n🔔 Set Alert\n❌ Clear Alert\n🆔 My ID\n📊 Status"
  );
});

// SET ALERT MODE
bot.onText(/set alert/i, (msg) => {
  safeSend(msg.chat.id, "💬 Send:\n70000 (above)\n-60000 (below)");
});

// CLEAR ALERT
bot.onText(/clear alert/i, (msg) => {
  delete userAlerts[msg.chat.id];
  saveData();
  safeSend(msg.chat.id, "🔕 Alert cleared");
});

// ===== HANDLE INPUT =====
bot.on("message", (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  if (!text) return;
  if (text.startsWith("/")) return;

  // NUMBER INPUT
  if (!isNaN(text)) {
    const value = parseFloat(text);

    userAlerts[chatId] = {
      price: Math.abs(value),
      type: value >= 0 ? "above" : "below",
    };

    saveData();

    safeSend(
      chatId,
      `🔔 Alert set for BTC ${userAlerts[chatId].type.toUpperCase()} $${Math.abs(
        value
      )}`
    );
  }
});

// ===== ALERT LOOP =====
setInterval(async () => {
  const price = await getBTCPrice();
  if (!price) return;

  for (let chatId in userAlerts) {
    const alert = userAlerts[chatId];

    if (
      (alert.type === "above" && price >= alert.price) ||
      (alert.type === "below" && price <= alert.price)
    ) {
      safeSend(
        chatId,
        `🚨 ALERT TRIGGERED\n💰 BTC: $${price}`
      );

      delete userAlerts[chatId];
      saveData();
    }
  }
}, 10000);

// ===== CRASH PROTECTION =====
process.on("uncaughtException", (err) => {
  console.error("Crash:", err.message);
});

process.on("unhandledRejection", (err) => {
  console.error("Promise crash:", err);
});
