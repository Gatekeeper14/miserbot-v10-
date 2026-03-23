require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const token = process.env.TELEGRAM_TOKEN;
const bot = new TelegramBot(token, { polling: true });

console.log("🔥 Miserbot V32 Multi-User Running...");

// =============================
// 🧠 MULTI USER STORAGE
// =============================
let users = {}; 
// structure:
// users = {
//   chatId: { alert: number }
// }

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

      users[chatId].alert = null; // clear after hit
    }
  }

}, 10000); // every 10 sec

// =============================
// 🚀 START MENU
// =============================
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;

  if (!users[chatId]) {
    users[chatId] = { alert: null };
  }

  bot.sendMessage(chatId,
    "🔥 Miserbot V32 Ready\nChoose an option:",
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

    bot.sendMessage(chatId,
      `🔔 Alert set for BTC = $${text}`
    );
  }
});
