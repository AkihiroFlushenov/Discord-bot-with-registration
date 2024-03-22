import discord
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, discord_id TEXT, hwid TEXT DEFAULT 'None', name TEXT, gmail TEXT, password TEXT, role TEXT DEFAULT 'User', subscription_time DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=None)


@bot.command()
async def change_time(ctx, member: discord.Member, subscription_type: str):
    if "ADMIN" in [role.name for role in ctx.author.roles]:
        if subscription_type == 'LifeTime':
            subscription_time = datetime(2100, 12, 21, 0, 0, 0)
        elif subscription_type == '3Months':
            subscription_time = datetime.now() + timedelta(days=90)
        elif subscription_type == '1Month':
            subscription_time = datetime.now() + timedelta(days=30)
        else:
            await ctx.send("Неверный тип подписки! Доступные типы: LifeTime, 3Months, 1Month.")
            return

        c.execute("UPDATE users SET subscription_time=? WHERE discord_id=?", (subscription_time.strftime('%Y-%m-%d %H:%M:%S'), str(member.id)))
        conn.commit()
        await ctx.send(f"Время подписки успешно обновлено для {member.display_name}!")
    else:
        await ctx.send("У вас нет разрешения на использование этой команды!")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def register(ctx, name: str, gmail: str, password: str):
    c.execute("SELECT * FROM users WHERE discord_id=?", (str(ctx.author.id),))
    user = c.fetchone()
    if user:
        await ctx.send("Вы уже зарегистрированы!")
    else:
        subscription_time = 0
        c.execute("INSERT INTO users (discord_id, name, gmail, password, subscription_time) VALUES (?, ?, ?, ?, ?)", (str(ctx.author.id), name, gmail, password, subscription_time))
        conn.commit()
        await ctx.send(f"Вы зарегистрированы, {ctx.author.name}!")


@bot.command()
async def change_password(ctx, new_password: str):
    c.execute("SELECT * FROM users WHERE discord_id=?", (str(ctx.author.id),))
    user = c.fetchone()
    if user:
        c.execute("UPDATE users SET password=? WHERE discord_id=?", (new_password, str(ctx.author.id)))
        conn.commit()
        try:
            await ctx.message.delete() 
            await ctx.author.send(f"Ваш пароль успешно обновлен: {new_password}")  
            await ctx.send("Пароль успешно обновлен!")
        except:
            await ctx.send("Не удалось отправить вам личное сообщение. Убедитесь, что у вас открыты личные сообщения в Discord.")
    else:
        await ctx.send("Вы не зарегистрированы! Пожалуйста, используйте !register зарегистрироваться.")

@bot.command()
async def change_role(ctx, member: discord.Member, new_role: str):
    if "ADMIN" in [role.name for role in ctx.author.roles]:
        if new_role:
            c.execute("UPDATE users SET role=? WHERE discord_id=?", (new_role, str(member.id)))
            conn.commit()
            await ctx.send(f"Роль успешно обновлена ​​для {member.display_name}!")
        else:
            await ctx.send("Неверная роль! Укажите допустимую роль.")
    else:
        await ctx.send("У вас нет разрешения на использование этой команды!")

@change_role.error
async def change_role_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Пожалуйста, укажите участника и новую роль!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Участник не найден!")

@bot.command()
async def profile(ctx):
    c.execute("SELECT * FROM users WHERE discord_id=?", (str(ctx.author.id),))
    user = c.fetchone()
    if user:
        if user[7] != 0 and datetime.now() > datetime.strptime(user[7], '%Y-%m-%d %H:%M:%S'):
            c.execute("UPDATE users SET subscription_time=?, role=? WHERE discord_id=?", (0, 'User', str(ctx.author.id)))
            conn.commit()
            user = c.fetchone() 
        embed = discord.Embed(title="Profile", color=discord.Color.dark_grey())
        embed.set_author(
            name="Akihiro",
            icon_url="https://media.discordapp.net/attachments/1220691440494055534/1220755800922914898/c75eaf4de3c5136daa86ab586bf72306.jpg?ex=6610186f&is=65fda36f&hm=2cf2db2230b67f48e377a2b82645a206992fab4285375feb467ad50a979a90d9&=&format=webp&width=600&height=675"
        )
        embed.add_field(name="ID", value=user[0])
        embed.add_field(name="Name", value=user[3])
        embed.add_field(name="Gmail", value=user[4], inline=False)
        embed.add_field(name="Role", value=user[6], inline=False)
        embed.add_field(name="Hwid", value=user[2])
        embed.add_field(name="Время подписки", value=user[7], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Вы не зарегистрированы! Пожалуйста, используйте !register для регистрации.")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Commands", color=discord.Color.dark_grey())
    embed.set_author(
        name="Akihiro",
        icon_url="https://media.discordapp.net/attachments/1220691440494055534/1220755800922914898/c75eaf4de3c5136daa86ab586bf72306.jpg?ex=6610186f&is=65fda36f&hm=2cf2db2230b67f48e377a2b82645a206992fab4285375feb467ad50a979a90d9&=&format=webp&width=600&height=675"
    )
    embed.add_field(name="!change_password", value="!change_password 123123", inline=False)
    embed.add_field(name="!register", value="!register Akihiro gmail@gmail.com 123123", inline=False)
    embed.add_field(name="!profile", value="Показывает информацию про вас", inline=False)
    embed.add_field(name="!price", value="Данная команда выводит сообщение с ценами.", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def price(ctx):
    embed = discord.Embed( title="Цены на покупку клиента.",color=discord.Color.dark_grey())
    embed.set_author(
        name="Akihiro",
        icon_url="https://media.discordapp.net/attachments/1220691440494055534/1220755800922914898/c75eaf4de3c5136daa86ab586bf72306.jpg?ex=6610186f&is=65fda36f&hm=2cf2db2230b67f48e377a2b82645a206992fab4285375feb467ad50a979a90d9&=&format=webp&width=600&height=675"
    )
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/1220691440494055534/1220756442357960744/-1.png?ex=66101908&is=65fda408&hm=21f6d32a78c66fb5e661b0c05b891dea2242e478f9293a21a1844309051ab1a5&=&format=webp&quality=lossless&width=550&height=550"
    )
    embed.add_field(name="Цены", value="Предзаказ LifeTime - 199 рублей.\nLifetime - 550 рублей.\n3 Months - 450 рублей.\n1 Months - 250 рублей.\nReset Hwid - 99 рублей.", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def reset_hwid(ctx, member: discord.Member):
    if "ADMIN" in [role.name for role in ctx.author.roles]:
        c.execute("UPDATE users SET hwid=? WHERE discord_id=?", ("None", str(member.id)))
        conn.commit()
        await ctx.send(f"HWID успешно обновлен для {member.display_name}!")
    else:
        await ctx.send("У вас нет разрешения на использование этой команды!")


@app.route('/hwid')
def get_hwid():
    hwid = request.args.get('hwid')
    c.execute("SELECT * FROM users WHERE hwid=?", (hwid,))
    users = c.fetchall()
    user_list = [{'id': user[0], 'discord_id': user[1], 'hwid': user[2], 'name': user[3], 'gmail': user[4], 'password': user[5], 'role': user[6], 'subscription_time': user[7]} for user in users]
    return jsonify(user_list)


@app.route('/login')
def login():
    name = request.args.get('name')
    password = request.args.get('password')
    c.execute("SELECT * FROM users WHERE name=? AND password=?", (name, password))
    user = c.fetchone()
    if user:
        user_info = {'id': user[0], 'discord_id': user[1], 'hwid': user[2], 'name': user[3], 'gmail': user[4], 'password': user[5], 'role': user[6], 'subscription_time': user[7]}
        return jsonify(user_info)
    else:
        return "User not found", 404

@app.route('/new_hwid', methods=['POST'])
def update_hwid():
    name = request.args.get('name')
    new_hwid = request.args.get('hwid')

    c.execute("SELECT hwid FROM users WHERE name=?", (name,))
    current_hwid = c.fetchone()
    if current_hwid[0] == 'None':
        c.execute("UPDATE users SET hwid=? WHERE name=?", (new_hwid, name))
        conn.commit()
        return "HWID updated successfully"
    else:
        return "Link already used"


def run_flask():
    #host='127.0.0.1', port=5000
    app.run()


if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    bot.run('MTIxODIxNTg2MTczOTk4Mjk3MQ.GTy6PQ.Jcokl9qFIT9nJ4cPV09xwHusTaX2R-nsqXXRkM')