import json
from xml.etree.ElementInclude import include
import requests
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
import asyncio
import nest_asyncio
import time
from discord.ext import tasks
import aiohttp
import re
from bs4 import BeautifulSoup

nest_asyncio.apply()
tokenjson = json.load(open('key/botToken.json', encoding = 'utf-8'))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

stream_code = int(tokenjson['stream_code']) # 디스코드 방송 알림 채널 코드
log_code = int(tokenjson['log_code']) # 디스코드 로그 채널 코드
title = ''
streamcheck = False

# @bot.command()
# async def leave(ctx):
#     if bot.voice_clients:
# 	    await bot.voice_clients[0].disconnect()

# @bot.command()
# async def play(ctx, urlorname):
#     channel = ctx.author.voice.channel
#     if channel == None:
#         await ctx.send("보이스 채널에 먼저 입장해주세요!")
#         return
    
#     if bot.voice_clients == [] or bot.voice_clients[0].channel != channel:
#         await channel.connect()
    
#     results = sp.search(urlorname, type='track', limit=1)
#     if len(results['tracks']['items']) > 0:
#         track = results['tracks']['items'][0]
#         track_name = track['name']
#         track_artist = track['artists'][0]['name']
#         track_preview_url = track['preview_url']
#         if track_preview_url:
#             bot.voice_clients[0].play(discord.FFmpegPCMAudio(track_preview_url))
#             await ctx.channel.send(f'재생 시작: {track_name} by {track_artist}')
#         else:
#             await ctx.channel.send('음악을 찾지 못했습니다!')
#     else:
#             await ctx.channel.send('음악을 찾지 못했습니다!')

# @bot.command()
# async def pause(ctx):
#     if not bot.voice_clients[0].is_paused():
#         bot.voice_clients[0].pause()
#     else:
#         await ctx.send("이미 일시정지 상태입니다!")

# @bot.command()
# async def resume(ctx):
#     if bot.voice_clients[0].is_paused():
#         bot.voice_clients[0].resume()
#     else:
#         await ctx.send("이미 재생 중 입니다!")ㄱ
        
# @bot.command()
# async def stop(ctx):
#     if bot.voice_clients[0].is_playing():
#         bot.voice_clients[0].stop()
#     else:
#     	await ctx.send("재생중인 음악이 없습니다!")


CHANNEL_ID = tokenjson['youtube_channel_id']
YOUTUBE_URL = 'https://www.youtube.com/@xfitgd'


@tasks.loop(seconds=60.0)
async def checklivestreams():
    streaming_link = f'{YOUTUBE_URL}/live'
    async with aiohttp.ClientSession() as session:
        async with session.get(streaming_link) as response:
            try:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                thum = soup.find("link",rel="image_src", href=True)['href']

                if "hqdefault_live.jpg" in thum:
                    print(f'방송을 시작했습니다! {streaming_link}')

                    title = soup.find("meta",property="og:title")['content']
                    embed = discord.Embed(
                                title=f":red_circle: 방송을 시작했습니다! : {title}",
                                color=discord.Color.blue(),
                                url=streaming_link)
                                                        
                    embed.set_image(url = thum)
                    embed.add_field(f"Youtube 방송 링크 : {streaming_link}")
                    embed.add_field("Kick 방송 링크 : https://kick.com/xfit")

                    await bot.get_channel(int(tokenjson['stream_code'])).send(embed=embed)
            except:
                return
                


@tasks.loop(seconds=60.0)
async def checkforvideos():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{YOUTUBE_URL}/videos") as response:#단축링크 사용 ㄴㄴ
            html = await response.text()
            try:
                latest_video_url = "https://www.youtube.com/watch?v=" + re.search('(?<="videoId":").*?(?=")', html).group()
            except:
                return

            if not str(tokenjson["latest_video_url"]) == latest_video_url:
                tokenjson['latest_video_url'] = latest_video_url

                with open('key/botToken.json', "w", encoding = 'utf-8') as f:
                    json.dump(tokenjson, f)
                    await bot.get_channel(int(tokenjson['youtube_code'])).send(f"유튜브 영상이 업로드되었습니다!\n{latest_video_url}")


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    checkforvideos.start()
    checklivestreams.start()

@bot.command()
async def ping(ctx):
    await ctx.send(f'pong! {round(bot.latency*1000, 4)}ms')


@bot.command()
@has_permissions(manage_messages=True)
async def rm(ctx, number = 1):
    await ctx.channel.purge(limit=(number+1))#명령 메시지까지 삭제

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("명령을 실행할 권한이 없습니다! 매니저에게 문의해주세요.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("유저 잘못됨!")
    else:
        raise error

@bot.event
async def on_message_delete(message):
    if message.channel.id != log_code and (not message.author.bot):
        embed=discord.Embed(title="{} 삭제한 메시지".format(message.author.name), description="", color=discord.Color.blue())
        embed.add_field(name= message.content ,value="", inline=True)
        await bot.get_channel(log_code).send(embed=embed)

@bot.event
async def on_message_edit(message_before, message_after):
    if message_before.channel.id != log_code and (not message_before.author.bot):
        embed=discord.Embed(title="{} 수정된 메시지".format(message_before.author.name), description="", color=discord.Color.blue())
        embed.add_field(name=message_before.content ,value="전", inline=True)
        embed.add_field(name=message_after.content ,value="후", inline=True)
        await bot.get_channel(log_code).send(embed=embed)

bot.run(tokenjson['token'])