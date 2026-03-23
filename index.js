const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

// ===== USER STATE =====
let users = {};

// ===== SAFE SEND =====
function send(chatId, text) {
  bot.sendMessage(chatId, text).catch(() => {});
}

// ===== BTC PRICE =====
async function getBTC() {
  try {
    const res = await axios.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT");
    return parseFloat(res.data.price);
  } catch {
    try {
      const res = await axios.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd");
      return res.data.bitcoin.usd;
    } catch {
      return null;
    }
  }
}

// ===== MENUS =====

function mainMenu(chatId) {
  users[chatId].mode = "main";

  send(chatId,
`👑 Miserbot X

1. 💰 Trading
2. ❤️ Family
3. 💳 Credit
4. ⚙️ Status
5. 🤖 Auto Mode

Type a number or name`);
}

function tradingMenu(chatId) {
  users[chatId].mode = "trading";

  send(chatId,
`💰 Trading Hub

1. BTC Price
2. Set Alert
3. Back`);
}

function familyMenu(chatId) {
  users[chatId].mode = "family";

  send(chatId,
`❤️ Family Assistant

1. Add Member
2. List Members
3. Send Check-in
4. Back`);
}

function creditMenu(chatId) {
  users[chatId].mode = "credit";

  send(chatId,
`💳 Credit System

1. Start Plan
2. Next Step
3. Progress
4. Back`);
}

function autoMenu(chatId) {
  users[chatId].mode = "auto";

  send(chatId,
`🤖 Auto Mode

1. Enable
2. Disable
3. Back`);
}

// ===== MAIN HANDLER =====

bot.on("message", async (msg) => {
  try {
    if (!msg.text) return;

    const chatId = msg.chat.id;
    const text = msg.text.toLowerCase();

    // INIT
    if (!users[chatId]) {
      users[chatId] = {
        mode: "main",
        auto: false,
        lastCheck: 0,
        alert: null,
        credit: { started: false, day: 1 },
        family: { members: [], step: null }
      };
      return mainMenu(chatId);
    }

    const user = users[chatId];
    const mode = user.mode;

    // ===== GLOBAL =====
    if (text === "/start" || text === "menu") return mainMenu(chatId);

    if (text === "status") return send(chatId, `✅ Running\nAuto: ${user.auto ? "ON" : "OFF"}`);

    if (text.includes("my id")) return send(chatId, `🆔 ${chatId}`);

    // ===== MAIN =====
    if (mode === "main") {
      if (text.includes("1")) return tradingMenu(chatId);
      if (text.includes("2")) return familyMenu(chatId);
      if (text.includes("3")) return creditMenu(chatId);
      if (text.includes("5") || text.includes("auto")) return autoMenu(chatId);
    }

    // ===== TRADING =====
    if (mode === "trading") {

      if (text.includes("btc")) {
        const price = await getBTC();
        if (!price) return send(chatId, "❌ Price error");
        return send(chatId, `💰 BTC: $${price.toFixed(2)}`);
      }

      if (text.includes("alert")) {
        user.mode = "set_alert";
        return send(chatId, "🎯 Send BTC price (example: 70000)");
      }

      if (text.includes("back") || text.includes("3")) return mainMenu(chatId);
    }

    // SET ALERT INPUT
    if (mode === "set_alert") {
      const value = parseFloat(text);

      if (!value) return send(chatId, "❌ Invalid number");

      user.alert = value;
      user.mode = "trading";

      return send(chatId, `🔔 Alert set at $${value}`);
    }

    // ===== FAMILY =====
    if (mode === "family") {

      if (user.family.step === "name") {
        user.family.temp = msg.text;
        user.family.step = "id";
        return send(chatId, "Send Chat ID");
      }

      if (user.family.step === "id") {
        user.family.members.push({ name: user.family.temp, id: msg.text });
        user.family.step = null;
        return send(chatId, "✅ Added");
      }

      if (text.includes("add")) {
        user.family.step = "name";
        return send(chatId, "Send name");
      }

      if (text.includes("list")) {
        let out = "Members:\n";
        user.family.members.forEach(m => out += m.name + "\n");
        return send(chatId, out || "None");
      }

      if (text.includes("check")) {
        user.family.members.forEach(m => {
          send(m.id, "❤️ Checking in on you!");
        });
        return send(chatId, "✅ Sent");
      }

      if (text.includes("back") || text.includes("4")) return mainMenu(chatId);
    }

    // ===== CREDIT =====
    if (mode === "credit") {

      if (text.includes("start")) {
        user.credit.started = true;
        user.credit.day = 1;
        return send(chatId, "Day 1: Check report");
      }

      if (text.includes("next")) {
        user.credit.day++;
        return send(chatId, `Day ${user.credit.day}`);
      }

      if (text.includes("back") || text.includes("4")) return mainMenu(chatId);
    }

    // ===== AUTO MODE =====
    if (mode === "auto") {

      if (text.includes("enable")) {
        user.auto = true;
        return send(chatId, "🤖 Auto Mode ON");
      }

      if (text.includes("disable")) {
        user.auto = false;
        return send(chatId, "🛑 Auto Mode OFF");
      }

      if (text.includes("back") || text.includes("3")) return mainMenu(chatId);
    }

  } catch (err) {
    console.log(err.message);
  }
});

// ===== WATCHDOG LOOP =====
setInterval(async () => {

  const price = await getBTC();
  if (!price) return;

  Object.keys(users).forEach(chatId => {
    const user = users[chatId];

    if (!user.auto) return;

    const now = Date.now();

    // Avoid spam (1 min cooldown)
    if (now - user.lastCheck < 60000) return;

    user.lastCheck = now;

    // BTC ALERT
    if (user.alert && price >= user.alert) {
      send(chatId, `🚨 BTC HIT $${price}`);
      user.alert = null;
    }

    // FAMILY CHECK (every 10 min)
    if (!user.lastFamily || now - user.lastFamily > 600000) {
      user.lastFamily = now;

      user.family.members.forEach(m => {
        send(m.id, "❤️ Auto check-in: thinking of you!");
      });
    }

  });

}, 60000);

console.log("🔥 Miserbot V43 AUTO running");
