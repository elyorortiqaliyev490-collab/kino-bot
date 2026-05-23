import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.environ.get("TOKEN")
TMDB_KEY = os.environ.get("TMDB_KEY")
TMDB = "https://api.themoviedb.org/3"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Kino Botga xush kelibsiz!\n\n"
        "🎥 /kino [nom] — Kino qidirish\n"
        "🌟 /aktyor [ism] — Aktyor qidirish\n\n"
        "Yoki shunchay kino nomini yozing!"
    )

async def kino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Masalan: /kino Inception")
        return
    res = requests.get(f"{TMDB}/search/movie", params={"api_key": TMDB_KEY, "query": query, "language": "ru-RU"}).json()
    if not res["results"]:
        await update.message.reply_text("Kino topilmadi!")
        return
    movie_id = res["results"][0]["id"]
    d = requests.get(f"{TMDB}/movie/{movie_id}", params={"api_key": TMDB_KEY, "language": "ru-RU"}).json()
    title = d.get("title", "?")
    year = d.get("release_date", "")[:4]
    rating = d.get("vote_average", 0)
    runtime = d.get("runtime", 0)
    genres = ", ".join([g["name"] for g in d.get("genres", [])])
    overview = d.get("overview", "Malumot yoq")
    poster = d.get("poster_path")
    text = f"🎬 {title} ({year})\n\nReyting: {rating:.1f}/10\nDavomiyligi: {runtime} daqiqa\nJanr: {genres}\n\n{overview[:500]}"
    keyboard = [[InlineKeyboardButton("Aktyorlar", callback_data=f"cast_{movie_id}")]]
    markup = InlineKeyboardMarkup(keyboard)
    if poster:
        await update.message.reply_photo(photo=f"https://image.tmdb.org/t/p/w500{poster}", caption=text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

async def aktyor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Masalan: /aktyor Tom Hanks")
        return
    res = requests.get(f"{TMDB}/search/person", params={"api_key": TMDB_KEY, "query": query}).json()
    if not res["results"]:
        await update.message.reply_text("Aktyor topilmadi!")
        return
    person_id = res["results"][0]["id"]
    d = requests.get(f"{TMDB}/person/{person_id}", params={"api_key": TMDB_KEY, "language": "ru-RU"}).json()
    name = d.get("name", "?")
    birthday = d.get("birthday", "Noma'lum")
    place = d.get("place_of_birth", "Noma'lum")
    bio = d.get("biography", "Malumot yoq")
    photo = d.get("profile_path")
    movies = requests.get(f"{TMDB}/person/{person_id}/movie_credits", params={"api_key": TMDB_KEY, "language": "ru-RU"}).json()
    top = sorted(movies.get("cast", []), key=lambda x: x.get("popularity", 0), reverse=True)[:5]
    films = "\n".join([f"{m['title']} ({m.get('release_date','')[:4]})" for m in top])
    text = f"🌟 {name}\n\nTugilgan: {birthday}\nJoy: {place}\n\nFilmlari:\n{films}\n\n{bio[:400]}"
    if photo:
        await update.message.reply_photo(photo=f"https://image.tmdb.org/t/p/w500{photo}", caption=text)
    else:
        await update.message.reply_text(text)

async def cast_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    movie_id = query.data.split("_")[1]
    data = requests.get(f"{TMDB}/movie/{movie_id}/credits", params={"api_key": TMDB_KEY, "language": "ru-RU"}).json()
    cast = data.get("cast", [])[:10]
    text = "Aktyorlar:\n\n" + "\n".join([f"{c['name']} - {c.get('character','')}" for c in cast])
    await query.message.reply_text(text)

async def xabar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.args = update.message.text.split()
    await kino(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kino", kino))
    app.add_handler(CommandHandler("aktyor", aktyor))
    app.add_handler(CallbackQueryHandler(cast_button, pattern="^cast_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, xabar))
    print("Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
