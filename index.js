require('dotenv').config();

const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 Miserbot V31 starting...");

// ===== STORAGE =====
let userAlert = null;
let userChatId = null;

// ===== MENU =====
const mainMenu = {
  reply_markup: {
    keyboard: [
      ["🚀 Start", "📊 Status"],
      ["💰 BTC Price", "🔔 Set Alert"],
      ["🔕 Clear Alert", "🆔 My ID"],
      ["❓ Help"]
    ],
    resize_keyboard: true
  }
};

// ===== FETCH BTC =====
async function getBTC() {
  try {
    const res = await axios.get(
      'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
    );
    return res.data.bitcoin.usd;
  } catch {
    return null;
  }
}

// ===== START =====
bot.onText(/\/start|🚀 Start/i, (msg) => {
  userChatId = msg.chat.id;
  bot.sendMessage(msg.chat.id, "🔥 Miserbot V31 Ready", mainMenu);
});

// ===== SHOW CHAT ID =====
bot.onText(/\/id|🆔 My ID/i, (msg) => {
  userChatId = msg.chat.id;
  bot.sendMessage(msg.chat.id, `🆔 Your Chat ID: ${msg.chat.id}`);
});

// ===== BTC PRICE =====
bot.onText(/BTC Price/i, async (msg) => {
  const price = await getBTC();

  if (!price) {
    bot.sendMessage(msg.chat.id, "⚠️ Try again...");
    return;
  }

  bot.sendMessage(msg.chat.id, `💰 BTC: $${price.toLocaleString()}`);
});

// ===== SET ALERT =====
bot.onText(/🔔 Set Alert/i, (msg) => {
  userChatId = msg.chat.id;
  bot.sendMessage(msg.chat.id, "💬 Send BTC price (example: 70000)");
});

// ===== CLEAR ALERT =====
bot.onText(/🔕 Clear Alert/i, (msg) => {
  userAlert = null;
  bot.sendMessage(msg.chat.id, "🔕 Alert cleared.");
});

// ===== STATUS =====
bot.onText(/📊 Status/i, (msg) => {
  bot.sendMessage(msg.chat.id, "✅ Bot running.");
});

// ===== HELP =====
bot.onText(/❓ Help/i, (msg) => {
  bot.sendMessage(msg.chat.id,
    "Set an alert and I’ll notify you when BTC hits your target 📈",
    mainMenu
  );
});

// ===== CAPTURE NUMBER INPUT =====
bot.on('message', (msg) => {
  const text = msg.text;

  if (!text || isNaN(text)) return;

  userAlert = parseInt(text);
  userChatId = msg.chat.id;

  bot.sendMessage(msg.chat.id, `🔔 Alert set for BTC = $${userAlert}`);
});

// ===== ALERT WATCHER =====
setInterval(async () => {
  if (!userAlert || !userChatId) return;

  const price = await getBTC();
  if (!price) return;

  if (price >= userAlert) {
    bot.sendMessage(userChatId,
      `🚨 BTC HIT TARGET!\n💰 Price: $${price.toLocaleString()}`
    );

    userAlert = null; // reset after trigger
  }
}, 30000); // every 30 seconds
