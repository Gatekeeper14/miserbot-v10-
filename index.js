const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

// ===== STORAGE =====
let users = {};
let history = { BTC: [], ETH: [] };

// ===== CONFIG =====
const INTERVAL = 15000;
const COOLDOWN = 60000;

// ===== SAFE SEND =====
function send(chatId, text) {
  bot.sendMessage(chatId, text).catch(() => {});
}

// ===== PRICE FETCH =====
async function getPrices() {
  try {
    const res = await axios.get(
      "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",
      { timeout: 5000 }
    );

    return {
      BTC: res.data.bitcoin.usd,
      ETH: res.data.ethereum.usd
    };
  } catch (err) {
    console.log("API error:", err.message);
    return null;
  }
}

// ===== HISTORY =====
function updateHistory(symbol, price) {
  history[symbol].push(price);
  if (history[symbol].length > 50) history[symbol].shift();
}

// ===== RSI =====
function calculateRSI(symbol, period = 14) {
  const data = history[symbol];
  if (data.length < period + 1) return null;

  let gains = 0, losses = 0;

  for (let i = data.length - period; i < data.length; i++) {
    const diff = data[i] - data[i - 1];
    if (diff > 0) gains += diff;
    else losses += Math.abs(diff);
  }

  if (losses === 0) return 100;

  const rs = (gains / period) / (losses / period);
  return 100 - (100 / (1 + rs));
}

// ===== SIGNAL =====
function getSignal(rsi) {
  if (!rsi) return "WAIT";
  if (rsi > 70) return "SELL 🔴";
  if (rsi < 30) return "BUY 🟢";
  return "HOLD 🤖";
}

// ===== AUTO LOOP =====
setInterval(async () => {
  try {
    const prices = await getPrices();
    if (!prices) return;

    for (let coin in prices) {
      updateHistory(coin, prices[coin]);
    }

    for (let chatId in users) {
      const user = users[chatId];
      if (!user.auto) continue;

      for (let coin of ["BTC", "ETH"]) {
        const price = prices[coin];
        const rsi = calculateRSI(coin);
        const signal = getSignal(rsi);

        const now = Date.now();
        if (user.lastTime && now - user.lastTime < COOLDOWN) continue;

        if (signal !== user.lastSignal && signal !== "WAIT") {
          user.lastSignal = signal;
          user.lastTime = now;

          send(chatId,
`🤖 AUTO SIGNAL (${coin})

💰 Price: $${price}
📊 RSI: ${rsi ? rsi.toFixed(2) : "..."}
🚦 ${signal}`);

          // PAPER TRADE
          if (signal.includes("BUY")) {
            user.position = coin;
            user.entry = price;
          }

          if (signal.includes("SELL") && user.position === coin) {
            const profit = price - user.entry;
            send(chatId,
`💸 TRADE CLOSED (${coin})

Entry: $${user.entry}
Exit: $${price}
PnL: $${profit.toFixed(2)}`);

            user.position = null;
            user.entry = null;
          }
        }
      }
    }

  } catch (err) {
    console.log("Loop error:", err.message);
  }
}, INTERVAL);

// ===== COMMAND HANDLER =====
bot.on("message", async (msg) => {
  try {
    if (!msg.text) return;

    const chatId = msg.chat.id;
    const text = msg.text.toLowerCase();

    if (!users[chatId]) users[chatId] = { auto: false };

    if (text.includes("help")) {
      send(chatId,
`📖 COMMANDS
💰 BTC Price
💰 ETH Price
🤖 Auto Mode
❌ Stop Auto
📊 Status
🆔 My ID`);
    }

    else if (text.includes("id")) {
      send(chatId, `🆔 ${chatId}`);
    }

    else if (text.includes("status")) {
      send(chatId, "✅ Bot running");
    }

    else if (text.includes("btc")) {
      const p = await getPrices();
      if (!p) return send(chatId, "❌ Price error");
      send(chatId, `💰 BTC: $${p.BTC}`);
    }

    else if (text.includes("eth")) {
      const p = await getPrices();
      if (!p) return send(chatId, "❌ Price error");
      send(chatId, `💰 ETH: $${p.ETH}`);
    }

    else if (text.includes("auto")) {
      users[chatId].auto = true;
      send(chatId, "🤖 AUTO MODE ON");
    }

    else if (text.includes("stop")) {
      users[chatId].auto = false;
      send(chatId, "❌ AUTO MODE OFF");
    }

  } catch (err) {
    console.log("Message error:", err.message);
  }
});

console.log("🔥 V43 FIXED RUNNING");
