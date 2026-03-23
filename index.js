require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const fs = require('fs');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🔥 Miserbot V33 Persistent Running...");

// =============================
// 📁 FILE STORAGE
// =============================
const DATA_FILE = 'users.json';

// Load users from file
let users = {};

function loadUsers() {
  try {
    if (fs.existsSync(DATA_FILE)) {
      const data = fs.readFileSync(DATA_FILE);
      users = JSON.parse(data);
      console.log("✅ Users loaded");
    }
  } catch (err) {
    console.log("❌ Failed to load users");
  }
}

// Save users to file
function saveUsers() {
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(users, null, 2));
  } catch (err) {
    console.log("❌ Failed to save users");
  }
}

// Load on startup
loadUsers();

// =============================
// 📊 GET BTC PRICE
// =============================
async function getBTCPrice() {
  try {
    const res = await axios.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd');
    return res.data.bitcoin.usd;
  } catch (err) {
    return null;
  }
}

// =============================
// 🔔 CHECK ALERTS LOOP
// =============================
setInterval(async () => {
  const price = await getBTCPrice();
  if (!price) return;

  for (let chatId in users) {
    const user = users[chatId];

    if (user.alert && price >= user.alert) {
      bot.sendMessage(chatId,
        `🚨 BTC HIT TARGET!\n💰 Price: $${price}`
      );

      users[chatId].alert = null;
      saveUsers(); // save after trigger
    }
  }

}, 10000);

// =============================
// 🚀 START MENU
// =============================
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;

  if (!users[chatId]) {
    users[chatId] = { alert: null };
    saveUsers();
  }

  bot.sendMessage(chatId,
    "🔥 Miserbot V33 Ready\nChoose an option:",
    {
      reply_markup: {
        keyboard: [
          ["💰 BTC Price", "🔔 Set Alert"],
          ["❌ Clear Alert", "🆔 My ID"],
          ["📊 Status", "❓ Help"]
        ],
        resize_keyboard: true
      }
    }
  );
});

// =============================
// 💰 BTC PRICE
// =============================
bot.onText(/BTC Price/, async (msg) => {
  const chatId = msg.chat.id;
  const price = await getBTCPrice();

  if (!price) {
    return bot.sendMessage(chatId, "❌ Failed to fetch BTC price.");
  }

  bot.sendMessage(chatId, `💰 BTC: $${price}`);
});

// =============================
// 🔔 SET ALERT
// =============================
bot.onText(/Set Alert/, (msg) => {
  const chatId = msg.chat.id;

  bot.sendMessage(chatId,
    "💬 Send BTC price (example: 70000)"
  );
});

// =============================
// ❌ CLEAR ALERT
// =============================
bot.onText(/Clear Alert/, (msg) => {
  const chatId = msg.chat.id;

  if (users[chatId]) {
    users[chatId].alert = null;
    saveUsers();
  }

  bot.sendMessage(chatId, "🚫 Alert cleared.");
});

// =============================
// 🆔 GET ID
// =============================
bot.onText(/My ID/, (msg) => {
  bot.sendMessage(msg.chat.id, `🆔 Your Chat ID: ${msg.chat.id}`);
});

// =============================
// 📊 STATUS
// =============================
bot.onText(/Status/, (msg) => {
  bot.sendMessage(msg.chat.id, "✅ Bot running.");
});

// =============================
// ❓ HELP
// =============================
bot.onText(/Help/, (msg) => {
  bot.sendMessage(msg.chat.id,
`Commands:
/start
BTC Price
Set Alert
Clear Alert
My ID`
  );
});

// =============================
// 🎯 CAPTURE NUMBER INPUT
// =============================
bot.on('message', (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  if (!users[chatId]) {
    users[chatId] = { alert: null };
  }

  if (!isNaN(text)) {
    users[chatId].alert = Number(text);
    saveUsers(); // save when user sets alert

    bot.sendMessage(chatId,
      `🔔 Alert set for BTC = $${text}`
    );
  }
});
