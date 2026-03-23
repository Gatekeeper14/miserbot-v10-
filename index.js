const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");
const fs = require("fs");

const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, { polling: true });

// ===== SAFE SEND =====
function safeSend(chatId, text) {
  bot.sendMessage(chatId, text).catch(() => {});
}

// ===== STORAGE =====
let userAlerts = {};
let lastSignalSent = {};
const FILE = "alerts.json";

function loadData() {
  try {
    if (fs.existsSync(FILE)) {
      userAlerts = JSON.parse(fs.readFileSync(FILE));
    }
  } catch {}
}

function saveData() {
  try {
    fs.writeFileSync(FILE, JSON.stringify(userAlerts, null, 2));
  } catch {}
}

loadData();

// ===== BTC PRICE (MULTI API) =====
async function getBTCPrice() {
  try {
    const res = await axios.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT");
    return parseFloat(res.data.price);
  } catch {}

  try {
    const res = await axios.get("https://api.coinbase.com/v2/prices/BTC-USD/spot");
    return parseFloat(res.data.data.amount);
  } catch {}

  try {
    const res = await axios.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd");
    return res.data.bitcoin.usd;
  } catch {}

  throw new Error("All APIs failed");
}

// ===== PRO TRADER ENGINE =====
let priceHistory = [];

function addPrice(price) {
  priceHistory.push(price);
  if (priceHistory.length > 50) priceHistory.shift();
}

function movingAverage(period) {
  if (priceHistory.length < period) return null;
  const slice = priceHistory.slice(-period);
  return slice.reduce((a, b) => a + b, 0) / period;
}

function calculateRSI(period = 14) {
  if (priceHistory.length < period + 1) return null;

  let gains = 0;
  let losses = 0;

  for (let i = priceHistory.length - period; i < priceHistory.length; i++) {
    const diff = priceHistory[i] - priceHistory[i - 1];
    if (diff > 0) gains += diff;
    else losses += Math.abs(diff);
  }

  const avgGain = gains / period;
  const avgLoss = losses / period;

  if (avgLoss === 0) return 100;

  const rs = avgGain / avgLoss;
  return 100 - (100 / (1 + rs));
}

function getSignal() {
  const shortMA = movingAverage(5);
  const longMA = movingAverage(15);
  const rsi = calculateRSI();

  if (!shortMA || !longMA || !rsi) {
    return { signal: "WAIT", trend: "Collecting...", rsi: null };
  }

  let signal = "HOLD";
  let trend = "SIDEWAYS";

  if (shortMA > longMA) trend = "📈 Uptrend";
  if (shortMA < longMA) trend = "📉 Downtrend";

  if (rsi < 30 && shortMA > longMA) signal = "🟢 STRONG BUY";
  else if (rsi > 70 && shortMA < longMA) signal = "🔴 STRONG SELL";
  else if (rsi < 30) signal = "🟢 BUY";
  else if (rsi > 70) signal = "🔴 SELL";

  return {
    signal,
    trend,
    rsi: rsi ? rsi.toFixed(2) : null
  };
}

// ===== COMMANDS =====
bot.onText(/\/start/, (msg) => {
  safeSend(msg.chat.id, "🔥 Miserbot V38 Autopilot Online");
});

// BTC PRICE + SIGNAL
bot.onText(/BTC Price/, async (msg) => {
  try {
    const price = await getBTCPrice();
    addPrice(price);
    const a = getSignal();

    safeSend(msg.chat.id,
      `💰 BTC: $${price.toFixed(2)}\n` +
      `📊 ${a.trend}\n` +
      `📉 RSI: ${a.rsi || "..."}\n` +
      `🤖 ${a.signal}`
    );
  } catch {
    safeSend(msg.chat.id, "❌ Failed to fetch BTC price");
  }
});

// SET ALERT
bot.onText(/Set Alert/, (msg) => {
  safeSend(msg.chat.id, "Send number:\n70000 (above)\n-60000 (below)");
});

bot.on("message", (msg) => {
  const text = msg.text;
  const chatId = msg.chat.id;

  if (!text) return;

  const num = parseFloat(text);

  if (!isNaN(num)) {
    userAlerts[chatId] = num;
    saveData();

    const type = num > 0 ? "ABOVE" : "BELOW";
    safeSend(chatId, `🔔 Alert set for BTC ${type} $${Math.abs(num)}`);
  }
});

// CLEAR ALERT
bot.onText(/Clear Alert/, (msg) => {
  delete userAlerts[msg.chat.id];
  saveData();
  safeSend(msg.chat.id, "❌ Alert cleared");
});

// STATUS
bot.onText(/Status/, (msg) => {
  safeSend(msg.chat.id, "✅ Bot running stable");
});

// ===== AUTOPILOT LOOP =====
setInterval(async () => {
  try {
    const price = await getBTCPrice();
    addPrice(price);
    const analysis = getSignal();

    for (let chatId in userAlerts) {
      const alert = userAlerts[chatId];

      // ALERT TRIGGER
      if (
        (alert > 0 && price >= alert) ||
        (alert < 0 && price <= Math.abs(alert))
      ) {
        safeSend(chatId,
          `🚨 ALERT HIT\n💰 BTC: $${price.toFixed(2)}\n🎯 Target: $${Math.abs(alert)}`
        );
        delete userAlerts[chatId];
        saveData();
      }

      // AUTO SIGNAL ALERT
      if (lastSignalSent[chatId] !== analysis.signal) {
        lastSignalSent[chatId] = analysis.signal;

        safeSend(chatId,
          `🤖 AUTO SIGNAL\n\n` +
          `💰 BTC: $${price.toFixed(2)}\n` +
          `📊 ${analysis.trend}\n` +
          `📉 RSI: ${analysis.rsi || "..."}\n` +
          `🚦 ${analysis.signal}`
        );
      }
    }

  } catch {}
}, 15000); // every 15 sec
