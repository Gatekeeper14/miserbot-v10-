const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");
const fs = require("fs");

const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, { polling: true });

// ===== LOAD / SAVE DATA =====
let userAlerts = {};

function loadData() {
  try {
    const data = fs.readFileSync("alerts.json");
    userAlerts = JSON.parse(data);
  } catch {
    userAlerts = {};
  }
}

function saveData() {
  fs.writeFileSync("alerts.json", JSON.stringify(userAlerts, null, 2));
}

loadData();

// ===== GET BTC PRICE =====
async function getBTCPrice() {
  try {
    const res = await axios.get(
      "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    );
    return res.data.bitcoin.usd;
  } catch (err) {
    return null;
  }
}

// ===== START COMMAND =====
bot.onText(/\/start/, (msg) => {
  bot.sendMessage(msg.chat.id, "🔥 Miserbot V34 Ready", {
    reply_markup: {
      keyboard: [
        ["💰 BTC Price", "🔔 Set Alert"],
        ["🔕 Clear Alert", "🆔 My ID"],
        ["📊 Status"]
      ],
      resize_keyboard: true
    }
  });
});

// ===== BTC PRICE =====
bot.onText(/BTC Price/, async (msg) => {
  const price = await getBTCPrice();
  if (!price) {
    return bot.sendMessage(msg.chat.id, "❌ Failed to fetch BTC price");
  }
  bot.sendMessage(msg.chat.id, `💰 BTC: $${price}`);
});

// ===== SET ALERT =====
bot.onText(/Set Alert/, (msg) => {
  bot.sendMessage(msg.chat.id, "💬 Send BTC price (example: 70000)");
});

// ===== RECEIVE ALERT PRICE =====
bot.on("message", async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  if (!text || isNaN(text)) return;

  const priceTarget = parseFloat(text);
  const currentPrice = await getBTCPrice();

  if (!currentPrice) {
    return bot.sendMessage(chatId, "❌ Failed to fetch BTC price");
  }

  // Determine direction
  const direction = priceTarget > currentPrice ? "above" : "below";

  userAlerts[chatId] = {
    target: priceTarget,
    direction: direction,
    triggered: false,
    lastPrice: currentPrice
  };

  saveData();

  bot.sendMessage(
    chatId,
    `🔔 Alert set for BTC ${direction.toUpperCase()} $${priceTarget}`
  );
});

// ===== CLEAR ALERT =====
bot.onText(/Clear Alert/, (msg) => {
  const chatId = msg.chat.id;

  delete userAlerts[chatId];
  saveData();

  bot.sendMessage(chatId, "🔕 Alert cleared");
});

// ===== MY ID =====
bot.onText(/My ID/, (msg) => {
  bot.sendMessage(msg.chat.id, `🆔 Your Chat ID: ${msg.chat.id}`);
});

// ===== STATUS =====
bot.onText(/Status/, (msg) => {
  bot.sendMessage(msg.chat.id, "✅ Bot running");
});

// ===== SMART ALERT CHECK LOOP =====
setInterval(async () => {
  const price = await getBTCPrice();
  if (!price) return;

  for (let chatId in userAlerts) {
    const alert = userAlerts[chatId];

    if (alert.triggered) continue;

    // CROSSING LOGIC
    if (
      alert.direction === "above" &&
      alert.lastPrice < alert.target &&
      price >= alert.target
    ) {
      bot.sendMessage(
        chatId,
        `🚨 BTC CROSSED ABOVE!\n💰 Price: $${price}`
      );
      alert.triggered = true;
    }

    if (
      alert.direction === "below" &&
      alert.lastPrice > alert.target &&
      price <= alert.target
    ) {
      bot.sendMessage(
        chatId,
        `🚨 BTC DROPPED BELOW!\n💰 Price: $${price}`
      );
      alert.triggered = true;
    }

    alert.lastPrice = price;
  }

  saveData();
}, 10000);
