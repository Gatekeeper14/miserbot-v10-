const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");

// ===== ENV =====
const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, { polling: true });

// ===== STORAGE =====
let userAlerts = {};
let lastSignal = {}; // prevent spam

// ===== CONFIG =====
const CHECK_INTERVAL = 15000; // 15 sec
const SIGNAL_COOLDOWN = 60000; // 1 min per user

// ===== BTC PRICE =====
async function getBTC() {
  try {
    const res = await axios.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd");
    return res.data.bitcoin.usd;
  } catch {
    return null;
  }
}

// ===== RSI CALC (simple fake for now upgrade later) =====
function getRSI(price) {
  return Math.random() * (90 - 40) + 40; // simulate for now
}

// ===== AUTO SIGNAL ENGINE =====
async function autoSignalLoop() {
  const price = await getBTC();
  if (!price) return;

  const rsi = getRSI(price);

  let signal = "WAIT";

  if (rsi > 80) signal = "SELL 🔴";
  else if (rsi < 45) signal = "BUY 🟢";
  else signal = "HOLD 🤖";

  for (let chatId in userAlerts) {

    const now = Date.now();

    // cooldown check
    if (lastSignal[chatId] && now - lastSignal[chatId] < SIGNAL_COOLDOWN) continue;

    lastSignal[chatId] = now;

    bot.sendMessage(chatId,
`🤖 AUTO SIGNAL

💰 BTC: $${price}
📊 RSI: ${rsi.toFixed(2)}

📡 Signal: ${signal}`);
  }
}

// ===== RUN LOOP =====
setInterval(autoSignalLoop, CHECK_INTERVAL);

// ===== COMMAND HANDLER =====
bot.on("message", async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text.trim().toLowerCase();

  // ===== HELP =====
  if (text.includes("help")) {
    bot.sendMessage(chatId,
`📖 Commands:
💰 BTC Price
🔔 Set Alert
❌ Clear Alert
🆔 My ID
📊 Status`);
  }

  // ===== MY ID =====
  else if (text.includes("my id")) {
    bot.sendMessage(chatId, `🆔 ID: ${chatId}`);
  }

  // ===== STATUS =====
  else if (text.includes("status")) {
    bot.sendMessage(chatId, "✅ Bot running (AUTO MODE ON)");
  }

  // ===== BTC PRICE =====
  else if (text.includes("btc")) {
    const price = await getBTC();
    if (!price) {
      bot.sendMessage(chatId, "❌ Failed to fetch BTC price");
      return;
    }

    const rsi = getRSI(price);

    let trend = rsi > 70 ? "Uptrend 📈" : "Downtrend 📉";
    let signal = rsi > 80 ? "SELL 🔴" : rsi < 45 ? "BUY 🟢" : "HOLD 🤖";

    bot.sendMessage(chatId,
`💰 BTC: $${price}
${trend}
📊 RSI: ${rsi.toFixed(2)}
🤖 ${signal}`);
  }

  // ===== SET ALERT =====
  else if (text.includes("alert") && !text.includes("clear")) {
    userAlerts[chatId] = true;

    bot.sendMessage(chatId,
`🔔 AUTO MODE ENABLED

🤖 You will now receive signals automatically.`);
  }

  // ===== CLEAR ALERT =====
  else if (text.includes("clear")) {
    delete userAlerts[chatId];
    bot.sendMessage(chatId, "❌ Auto mode OFF");
  }
});

// ===== START MESSAGE =====
console.log("🔥 Miserbot V39 AUTO MODE running...");
