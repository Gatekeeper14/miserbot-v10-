const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

// ===== STORAGE =====
let users = {}; 
// { chatId: { auto: true, lastSignal: "", position: null, entry: null } }

// ===== CONFIG =====
const INTERVAL = 15000;
const COOLDOWN = 60000;

// ===== PRICE FETCH =====
async function getPrices() {
  try {
    const res = await axios.get(
      "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
    );
    return {
      BTC: res.data.bitcoin.usd,
      ETH: res.data.ethereum.usd
    };
  } catch {
    return null;
  }
}

// ===== REAL RSI =====
let history = { BTC: [], ETH: [] };

function updateHistory(symbol, price) {
  history[symbol].push(price);
  if (history[symbol].length > 50) history[symbol].shift();
}

function calculateRSI(symbol, period = 14) {
  const data = history[symbol];
  if (data.length < period + 1) return null;

  let gains = 0;
  let losses = 0;

  for (let i = data.length - period; i < data.length; i++) {
    const diff = data[i] - data[i - 1];
    if (diff > 0) gains += diff;
    else losses += Math.abs(diff);
  }

  const avgGain = gains / period;
  const avgLoss = losses / period;

  if (avgLoss === 0) return 100;

  const rs = avgGain / avgLoss;
  return 100 - (100 / (1 + rs));
}

// ===== SIGNAL ENGINE =====
function getSignal(rsi) {
  if (!rsi) return "WAIT";
  if (rsi > 70) return "SELL 🔴";
  if (rsi < 30) return "BUY 🟢";
  return "HOLD 🤖";
}

// ===== AUTO LOOP =====
setInterval(async () => {
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

        bot.sendMessage(chatId,
`🤖 AUTO SIGNAL (${coin})

💰 Price: $${price}
📊 RSI: ${rsi ? rsi.toFixed(2) : "..."}
🚦 Signal: ${signal}`);

        // ===== PAPER TRADING =====
        if (signal.includes("BUY")) {
          user.position = coin;
          user.entry = price;
        }

        if (signal.includes("SELL") && user.position === coin) {
          const profit = price - user.entry;
          bot.sendMessage(chatId,
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
}, INTERVAL);

// ===== COMMANDS =====
bot.on("message", async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text.toLowerCase();

  if (!users[chatId]) {
    users[chatId] = { auto: false };
  }

  // HELP
  if (text.includes("help")) {
    bot.sendMessage(chatId,
`📖 COMMANDS
💰 BTC Price
💰 ETH Price
🔔 Auto Mode
❌ Stop Auto
📊 Status
🆔 My ID`);
  }

  // ID
  else if (text.includes("id")) {
    bot.sendMessage(chatId, `🆔 ${chatId}`);
  }

  // STATUS
  else if (text.includes("status")) {
    bot.sendMessage(chatId, `✅ Running`);
  }

  // BTC
  else if (text.includes("btc")) {
    const p = await getPrices();
    bot.sendMessage(chatId, `💰 BTC: $${p.BTC}`);
  }

  // ETH
  else if (text.includes("eth")) {
    const p = await getPrices();
    bot.sendMessage(chatId, `💰 ETH: $${p.ETH}`);
  }

  // AUTO ON
  else if (text.includes("auto")) {
    users[chatId].auto = true;
    bot.sendMessage(chatId, "🤖 AUTO MODE ON");
  }

  // AUTO OFF
  else if (text.includes("stop")) {
    users[chatId].auto = false;
    bot.sendMessage(chatId, "❌ AUTO MODE OFF");
  }
});

console.log("🔥 Miserbot V43 MASTER running...");
