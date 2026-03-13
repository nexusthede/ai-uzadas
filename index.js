import { Client, GatewayIntentBits } from "discord.js";
import fetch from "node-fetch";

// ===== Bot Setup =====
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

// ===== Environment Variables =====
const TOKEN = process.env.DISCORD_TOKEN;
const LOCALAI_URL = process.env.LOCALAI_URL;
const ALLOWED_GUILD_ID = "1449708401050259457"; // your server ID

// ===== Memory per channel =====
let conversationMemory = {};

// ===== Bot triggers =====
const TRIGGERS = ["uza", "uzadas", "Uza", "Uzadas"];

// ===== Human-like typing delay =====
function humanDelay(messageLength) {
  const base = messageLength * 80;
  const random = Math.floor(Math.random() * 2000);
  return base + random;
}

// ===== Slang / Discord-style text =====
function slangify(text) {
  if (Math.random() < 0.5) text = text.toLowerCase();

  text = text
    .replace(/\bwhat is going on\b/gi, "wsg")
    .replace(/\bgoing\b/gi, "gng")
    .replace(/\byou\b/gi, "u")
    .replace(/\bfor real\b/gi, "fr")
    .replace(/\bnot gonna lie\b/gi, "ngl")
    .replace(/\blaugh out loud\b/gi, "lol");

  if (Math.random() < 0.2) {
    text = text.replace(/(\w)(\w)/, "$2$1");
  }

  if (Math.random() < 0.3) {
    const emojis = ["😂", "🙃", "😅", "✌️", "🤣"];
    const fillers = ["lol", "bruh", "haha", "ngl"];
    const pick = Math.random() < 0.5 ? emojis[Math.floor(Math.random()*emojis.length)] : fillers[Math.floor(Math.random()*fillers.length)];
    text += " " + pick;
  }

  if (Math.random() < 0.3) {
    text = text.replace(/[.,!?]/g, "");
  }

  return text;
}

// ===== Bot ready =====
client.on("ready", () => {
  console.log(`${client.user.tag} is online!`);
});

// ===== Auto-leave other servers =====
client.on("guildCreate", async (guild) => {
  if (guild.id !== ALLOWED_GUILD_ID) {
    console.log(`Left server: ${guild.name} (${guild.id}) — not allowed.`);
    await guild.leave();
  }
});

// ===== Message handler =====
client.on("messageCreate", async (message) => {
  if (message.author.bot) return;
  if (message.guild?.id !== ALLOWED_GUILD_ID) return;

  const lower = message.content.toLowerCase();
  if (!TRIGGERS.some(trigger => lower.includes(trigger.toLowerCase()))) return;

  if (!conversationMemory[message.channel.id]) conversationMemory[message.channel.id] = [];
  const mem = conversationMemory[message.channel.id];
  mem.push({ role: "user", content: message.content });
  if (mem.length > 10) mem.shift();

  const prompt = mem.map(m => m.content).join("\n");

  try {
    message.channel.sendTyping();

    const response = await fetch(LOCALAI_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "vicuna-7b",
        prompt: prompt,
        max_tokens: 300
      }),
    });

    const data = await response.json();
    let reply = data.choices[0].text || "idk lol";

    reply = slangify(reply);

    const delay = humanDelay(reply.length);
    setTimeout(() => message.reply(reply), delay);

  } catch (err) {
    console.error(err);
    message.reply("Oops, something went wrong 😅");
  }
});

// ===== Login =====
client.login(TOKEN);
