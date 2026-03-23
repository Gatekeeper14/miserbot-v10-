const TelegramBot = require("node-telegram-bot-api");
const axios = require("axios");

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

// 🔐 SET YOUR ADMIN ID
const ADMIN_ID = 8741545426;

// ===== USERS =====
let users = {};

// ===== SAFE SEND =====
function send(chatId, text) {
  bot.sendMessage(chatId, text).catch(() => {});
}

// ===== BTC =====
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

// ===== MENU =====

function mainMenu(chatId) {
  users[chatId].mode = "main";

  send(chatId,
`👑 Miserbot X

1. 💰 Trading
2. ❤️ Family
3. 💳 Credit
4. ⚙️ Status
5. 🤖 Auto Mode
6. 💎 Upgrade

Type a number or name`);
}

function tradingMenu(chatId) {
  users[chatId].mode = "trading";

  send(chatId,
`💰 Trading Hub

1. BTC Price
2. Set Alert 🔒
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
`🤖 Auto Mode 🔒

1. Enable
2. Disable
3. Back`);
}

// ===== MAIN =====

bot.on("message", async (msg) => {
  try {
    if (!msg.text) return;

    const chatId = msg.chat.id;
    const text = msg.text.toLowerCase();

    // INIT USER
    if (!users[chatId]) {
      users[chatId] = {
        mode: "main",
        premium: false,
        auto: false,
        alert: null,
        lastCheck: 0,
        credit: { started: false, day: 1 },
        family: { members: [], step: null }
      };
      return mainMenu(chatId);
    }

    const user = users[chatId];
    const mode = user.mode;

    // ===== ADMIN COMMAND =====
    if (chatId == ADMIN_ID && text.startsWith("unlock")) {
      const id = text.split(" ")[1];
      if (users[id]) {
        users[id].premium = true;
        send(id, "💎 You are now PREMIUM");
        return send(chatId, "✅ User upgraded");
      }
    }

    // ===== GLOBAL =====
    if (text === "/start" || text === "menu") return mainMenu(chatId);

    if (text === "status") {
      return send(chatId,
`✅ Running
Plan: ${user.premium ? "💎 PREMIUM" : "FREE"}`);
    }

    if (text.includes("my id")) return send(chatId, `🆔 ${chatId}`);

    if (text.includes("upgrade")) {
      return send(chatId,
`💎 PREMIUM FEATURES

✔ Auto Trading
✔ Alerts
✔ Auto Family Check-ins

Contact admin to upgrade`);
    }

    // ===== MAIN =====
    if (mode === "main") {
      if (text.includes("1")) return tradingMenu(chatId);
      if (text.includes("2")) return familyMenu(chatId);
      if (text.includes("3")) return creditMenu(chatId);
      if (text.includes("5")) return autoMenu(chatId);
    }

    // ===== TRADING =====
    if (mode === "trading") {

      if (text.includes("btc")) {
        const price = await getBTC();
        if (!price) return send(chatId, "❌ Price error");
        return send(chatId, `💰 BTC: $${price.toFixed(2)}`);
      }

      if (text.includes("alert")) {
        if (!user.premium) {
          return send(chatId, "🔒 Upgrade to use alerts");
        }
        user.mode = "set_alert";
        return send(chatId, "Send BTC price");
      }

      if (text.includes("back") || text.includes("3")) return mainMenu(chatId);
    }

    // SET ALERT
    if (mode === "set_alert") {
      user.alert = parseFloat(text);
      user.mode = "trading";
      return send(chatId, `🔔 Alert set`);
    }

    // ===== FAMILY =====
    if (mode === "family") {

      if (user.family.step === "name") {
        user.family.temp = msg.text;
        user.family.step = "id";
        return send(chatId, "Send ID");
      }

      if (user.family.step === "id") {
        user.family.members.push({ name: user.family.temp, id: msg.text });
        user.family.step = null;
        return send(chatId, "Added");
      }

      if (text.includes("add")) {
        user.family.step = "name";
        return send(chatId, "Send name");
      }

      if (text.includes("list")) {
        let out = "Members:\n";
        user.family.members.forEach(m => out += m.name + "\n");
        return send(chatId, out);
      }

      if (text.includes("check")) {
        user.family.members.forEach(m => {
          send(m.id, "❤️ Message from your assistant");
        });
        return send(chatId, "Sent");
      }

      if (text.includes("back") || text.includes("4")) return mainMenu(chatId);
    }

    // ===== CREDIT =====
    if (mode === "credit") {
      if (text.includes("start")) {
        user.credit.started = true;
        return send(chatId, "Day 1: Check report");
      }
      if (text.includes("next")) {
        user.credit.day++;
        return send(chatId, `Day ${user.credit.day}`);
      }
      if (text.includes("back") || text.includes("4")) return mainMenu(chatId);
    }

    // ===== AUTO =====
    if (mode === "auto") {

      if (!user.premium) {
        return send(chatId, "🔒 Upgrade to use Auto Mode");
      }

      if (text.includes("enable")) {
        user.auto = true;
        return send(chatId, "🤖 Auto ON");
      }

      if (text.includes("disable")) {
        user.auto = false;
        return send(chatId, "OFF");
      }

      if (text.includes("back") || text.includes("3")) return mainMenu(chatId);
    }

  } catch (e) {
    console.log(e.message);
  }
});

// ===== AUTO LOOP =====
setInterval(async () => {

  const price = await getBTC();
  if (!price) return;

  Object.keys(users).forEach(id => {
    const user = users[id];

    if (!user.auto || !user.premium) return;

    const now = Date.now();
    if (now - user.lastCheck < 60000) return;

    user.lastCheck = now;

    if (user.alert && price >= user.alert) {
      send(id, `🚨 BTC HIT $${price}`);
      user.alert = null;
    }

    if (user.family.members.length > 0) {
      user.family.members.forEach(m => {
        send(m.id, "❤️ Auto check-in");
      });
    }

  });

}, 60000);

console.log("🔥 Miserbot V44 PREMIUM running");
