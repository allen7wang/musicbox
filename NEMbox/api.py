#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: omi
# @Date:   2014-08-24 21:51:57
# @Last Modified by:   omi
# @Last Modified time: 2015-05-26 01:06:55


'''
网易云音乐 Api
'''

import re
import os
import json
import requests
from Crypto.Cipher import AES
import rsa
from bs4 import BeautifulSoup
import logger
import hashlib
import random
import base64

# 歌曲榜单地址
top_list_all={
    0:['云音乐新歌榜','/discover/toplist?id=3779629'],
    1:['云音乐热歌榜','/discover/toplist?id=3778678'],
    2:['网易原创歌曲榜','/discover/toplist?id=2884035'],
    3:['云音乐飙升榜','/discover/toplist?id=19723756'],
    4:['云音乐电音榜','/discover/toplist?id=10520166'],
    5:['UK排行榜周榜','/discover/toplist?id=180106'],
    6:['美国Billboard周榜','/discover/toplist?id=60198'],
    7:['KTV嗨榜','/discover/toplist?id=21845217'],
    8:['iTunes榜','/discover/toplist?id=11641012'],
    9:['Hit FM Top榜','/discover/toplist?id=120001'],
    10:['日本Oricon周榜','/discover/toplist?id=60131'],
    11:['韩国Melon排行榜周榜','/discover/toplist?id=3733003'],
    12:['韩国Mnet排行榜周榜','/discover/toplist?id=60255'],
    13:['韩国Melon原声周榜','/discover/toplist?id=46772709'],
    14:['中国TOP排行榜(港台榜)','/discover/toplist?id=112504'],
    15:['中国TOP排行榜(内地榜)','/discover/toplist?id=64016'],
    16:['香港电台中文歌曲龙虎榜','/discover/toplist?id=10169002'],
    17:['华语金曲榜','/discover/toplist?id=4395559'],
    18:['中国嘻哈榜','/discover/toplist?id=1899724'],
    19:['法国 NRJ EuroHot 30周榜','/discover/toplist?id=27135204'],
    20:['台湾Hito排行榜','/discover/toplist?id=112463'],
    21:['Beatport全球电子舞曲榜','/discover/toplist?id=3812895']
    }

default_timeout = 10

log = logger.getLogger(__name__)

# 歌曲加密算法, 基于https://github.com/yanunon/NeteaseCloudMusic脚本实现
def encrypted_id(id):
    magic = bytearray('3go8&$8*3*3h0k(2)2')
    song_id = bytearray(id)
    magic_len = len(magic)
    for i in xrange(len(song_id)):
        song_id[i] = song_id[i]^magic[i%magic_len]
    m = hashlib.md5(song_id)
    result = m.digest().encode('base64')[:-1]
    result = result.replace('/', '_')
    result = result.replace('+', '-')
    return result

# 登录加密算法, 基于https://github.com/stkevintan/nw_musicbox脚本实现
def encrypted_login(username, password):
    modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
    nonce = '0CoJUm6Qyw8W8jud'
    pubKey = '010001'
    pem = """-----BEGIN RSA PUBLIC KEY-----
    MIGJAoGBAOC1CfYlnfhkLbw1ZikBR33yJnfsFStf9orOYVu3tyUVKzqxeodq6opa
    p20uQXYp7E7jQfVhNfzPaVKAEE4DEuy9qSVXyThwEUr2ydBcT38MNoW3pGvuJVky
    V1zOELQk2BPP5IddPoIEe5fd71J0HVRrjiidxpNbPs4EYtsKIrjnAgMBAAE=
    OWRjNjkzNWIzZWNlMDQ2MmRiMGEyMmI4ZTcCBjAxMDAwMQ==
    -----END RSA PUBLIC KEY-----
    """
    text = {
        'username': username,
        'password': password,
        'rememberLogin': 'true'
    }
    text = hashlib.md5(json.dumps(text)).hexdigest()
    secKey = createSecretKey(16)
    encText = aesEncrypt(text, nonce)
    encText = aesEncrypt(encText, secKey)
    encText = base64.b64encode(encText)
    encSecKey = rsaEncrypt(secKey, pem)
    data = {
        'params': encText,
        'encSecKey': encSecKey
    }
    return data

def encrypted_phonelogin(username, password):
    modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
    nonce = '0CoJUm6Qyw8W8jud'
    pubKey = '010001'
    pem = """-----BEGIN RSA PUBLIC KEY-----
    MIGJAoGBAOC1CfYlnfhkLbw1ZikBR33yJnfsFStf9orOYVu3tyUVKzqxeodq6opa
    p20uQXYp7E7jQfVhNfzPaVKAEE4DEuy9qSVXyThwEUr2ydBcT38MNoW3pGvuJVky
    V1zOELQk2BPP5IddPoIEe5fd71J0HVRrjiidxpNbPs4EYtsKIrjnAgMBAAE=
    OWRjNjkzNWIzZWNlMDQ2MmRiMGEyMmI4ZTcCBjAxMDAwMQ==
    -----END RSA PUBLIC KEY-----
    """
    text = {
        'phone': username,
        'password': password,
        'rememberLogin': 'true'
    }
    text = hashlib.md5(json.dumps(text)).hexdigest()
    secKey = createSecretKey(16)
    encText = aesEncrypt(text, nonce)
    encText = aesEncrypt(encText, secKey)
    encText = base64.b64encode(encText)
    encSecKey = rsaEncrypt(secKey, pem)
    data = {
        'params': encText,
        'encSecKey': encSecKey
    }
    print(data)
    return data

def aesEncrypt(text, secKey):
    mode = AES.MODE_CBC
    encryptor = AES.new(secKey, mode, '0102030405060708')
    ciphertext = encryptor.encrypt(text)
    return ciphertext

def rsaEncrypt(secKey, pem):
    pubkey = rsa.PublicKey.load_pkcs1(pem)
    encText = rsa.encrypt(secKey, pubkey)
    encText = encText.decode('ISO-8859-1').encode('HEX')
    return encText

def createSecretKey(size):
    return (''.join(map(lambda xx: (hex(ord(xx))[2:]), os.urandom(size))))[0:16]

# list去重
def uniq(arr):
    arr2 = list(set(arr))
    arr2.sort(key=arr.index)
    return arr2

# 获取高音质mp3 url
def geturl(song):
    if song['hMusic']:
        music = song['hMusic']
        quality = 'HD'
    elif song['mMusic']:
        music = song['mMusic']
        quality = 'MD'
    elif song['lMusic']:
        music = song['lMusic']
        quality = 'LD'
    else:
        return song['mp3Url'], ''

    quality = quality + ' {0}k'.format(music['bitrate']/1000)
    song_id = str(music['dfsId'])
    enc_id = encrypted_id(song_id)
    url = "http://m%s.music.126.net/%s/%s.mp3"%(random.randrange(1,3), enc_id, song_id)
    return url, quality


class NetEase:
    def __init__(self):
        self.header = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/search/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'
        }
        self.cookies = {
            'appver': '1.5.2'
        }
        self.playlist_class_dict = {}

    def return_toplists(self):
        temp=[]
        for i in range(len(top_list_all)):
            temp.append(top_list_all[i][0])
        return temp

    def httpRequest(self, method, action, query=None, urlencoded=None, callback=None, timeout=None):
        connection = json.loads(self.rawHttpRequest(method, action, query, urlencoded, callback, timeout))
        return connection

    def rawHttpRequest(self, method, action, query=None, urlencoded=None, callback=None, timeout=None):
        if (method == 'GET'):
            url = action if (query == None) else (action + '?' + query)
            connection = requests.get(url, headers=self.header, timeout=default_timeout)

        elif (method == 'POST'):
            connection = requests.post(
                action,
                data=query,
                headers=self.header,
                timeout=default_timeout
            )

        connection.encoding = "UTF-8"
        return connection.text

    # 登录
    def login(self, username, password):
        pattern = re.compile(r'^0\d{2,3}\d{7,8}$|^1[34578]\d{9}$')
        if (pattern.match(username)):
            return self.phone_login(username, password)
        action = 'http://music.163.com/weapi/login/'
        # data = {
        #     'params':'QN2FMbwsIPjwPhDrqNIPQ7kUz9jnw4I6XaLwWPLJFY6V3jJqzmAaXBHOreIWctHBGk+ICB5IXTC6zlF4juOjoTfdauP26olOi/b3dF+GZMKFWmHekWwPU039w2RlrVMLlOmqdFheZ5b4jikcONZaNajpSodIJaRSkT/V79oGM3/GtljK2ESAntfTvZ3WbBcnAJ5h6pqZrHPhe4Y/PpWbBQ==',
        #     'encSecKey': '4a2313415c12a1f29bd3e2219bafcaf1f7e8d888f0209253e7239fa01eec544961931102850d4acf10f9c624319672e97f7fa7b1998bce0148e66184f8256f207bbedbcb58e13b6855b5479f79d5819ae4a0681c3289bd67f59e172c13af5fc63c48ce549bf125a05e8824e89070c84ef67f6583e8ce18d2b474b7782ff779ae'
        # }
        data = encrypted_login(username, password)
        try:
            return self.httpRequest('POST', action, data)
        except:
            return {'code': 501}

    # 手机登录
    def phone_login(self, username, password):
        action = 'http://music.163.com/weapi/login/cellphone'
        data = encrypted_phonelogin(username, password)
        try:
            return self.httpRequest('POST', action, data)
        except:
            return {'code': 501}

    # 用户歌单
    def user_playlist(self, uid, offset=0, limit=100):
        action = 'http://music.163.com/api/user/playlist/?offset=' + str(offset) + '&limit=' + str(limit) + '&uid=' + str(uid)
        try:
            data = self.httpRequest('GET', action)
            return data['playlist']
        except:
            return []

    # 搜索单曲(1)，歌手(100)，专辑(10)，歌单(1000)，用户(1002) *(type)*
    def search(self, s, stype=1, offset=0, total='true', limit=60):
        action = 'http://music.163.com/api/search/get'
        data = {
            's': s,
            'type': stype,
            'offset': offset,
            'total': total,
            'limit': 60
        }
        return self.httpRequest('POST', action, data)

    # 新碟上架 http://music.163.com/#/discover/album/
    def new_albums(self, offset=0, limit=50):
        action = 'http://music.163.com/api/album/new?area=ALL&offset=' + str(offset) + '&total=true&limit=' + str(limit)
        try:
            data = self.httpRequest('GET', action)
            return data['albums']
        except:
            return []

    # 歌单（网友精选碟） hot||new http://music.163.com/#/discover/playlist/
    def top_playlists(self, category='全部', order='hot', offset=0, limit=50):
        action = 'http://music.163.com/api/playlist/list?cat=' + category + '&order=' + order + '&offset=' + str(offset) + '&total=' + ('true' if offset else 'false') + '&limit=' + str(limit)
        try:
            data = self.httpRequest('GET', action)
            return data['playlists']
        except:
            return []

    # 分类歌单
    def playlist_classes(self):
        action = 'http://music.163.com/discover/playlist/'
        try:
            data = self.rawHttpRequest('GET', action)
            return data
        except:
            return []

    # 分类歌单中某一个分类的详情
    def playlist_class_detail(self):
        pass

    # 歌单详情
    def playlist_detail(self, playlist_id):
        action = 'http://music.163.com/api/playlist/detail?id=' + str(playlist_id)
        try:
            data = self.httpRequest('GET', action)
            return data['result']['tracks']
        except:
            return []

    # 热门歌手 http://music.163.com/#/discover/artist/
    def top_artists(self, offset=0, limit=100):
        action = 'http://music.163.com/api/artist/top?offset=' + str(offset) + '&total=false&limit=' + str(limit)
        try:
            data = self.httpRequest('GET', action)
            return data['artists']
        except:
            return []

    # 热门单曲 http://music.163.com/discover/toplist?id=
    def top_songlist(self,idx=0, offset=0, limit=100):
        action = 'http://music.163.com' + top_list_all[idx][1]
        try:
            connection = requests.get(action, headers=self.header, timeout=default_timeout)
            connection.encoding = 'UTF-8'
            songids = re.findall(r'/song\?id=(\d+)', connection.text)
            if songids == []:
                return []
            # 去重
            songids = uniq(songids)
            return self.songs_detail(songids)
        except:
            return []

    # 歌手单曲
    def artists(self, artist_id):
        action = 'http://music.163.com/api/artist/' + str(artist_id)
        try:
            data = self.httpRequest('GET', action)
            return data['hotSongs']
        except:
            return []

    # album id --> song id set
    def album(self, album_id):
        action = 'http://music.163.com/api/album/' + str(album_id)
        try:
            data = self.httpRequest('GET', action)
            return data['album']['songs']
        except:
            return []

    # song ids --> song urls ( details )
    def songs_detail(self, ids, offset=0):
        tmpids = ids[offset:]
        tmpids = tmpids[0:100]
        tmpids = map(str, tmpids)
        action = 'http://music.163.com/api/song/detail?ids=[' + (',').join(tmpids) + ']'
        try:
            data = self.httpRequest('GET', action)
            return data['songs']
        except:
            return []

    # song id --> song url ( details )
    def song_detail(self, music_id):
        action = "http://music.163.com/api/song/detail/?id=" + str(music_id) + "&ids=[" + str(music_id) + "]"
        try:
            data = self.httpRequest('GET', action)
            return data['songs']
        except:
            return []


    # 今日最热（0）, 本周最热（10），历史最热（20），最新节目（30）
    def djchannels(self, stype=0, offset=0, limit=50):
        action = 'http://music.163.com/discover/djchannel?type=' + str(stype) + '&offset=' + str(offset) + '&limit=' + str(limit)
        try:
            connection = requests.get(action, headers=self.header, timeout=default_timeout)
            connection.encoding = 'UTF-8'
            channelids = re.findall(r'/dj\?id=(\d+)', connection.text)
            channelids = uniq(channelids)
            return self.channel_detail(channelids)
        except:
            return []

    # DJchannel ( id, channel_name ) ids --> song urls ( details )
    # 将 channels 整理为 songs 类型
    def channel_detail(self, channelids, offset=0):
        channels = []
        for i in range(0, len(channelids)):
            action = 'http://music.163.com/api/dj/program/detail?id=' + str(channelids[i])
            try:
                data = self.httpRequest('GET', action)
                channel = self.dig_info(data['program']['mainSong'], 'channels')
                channels.append(channel)
            except:
                continue

        return channels

    def dig_info(self, data, dig_type):
        temp = []
        if dig_type == 'songs':
            for i in range(0, len(data)):
                url, quality = geturl(data[i])
                
                if data[i]['album'] != None:
                    album_name = data[i]['album']['name']
                else:
                    album_name = '未知专辑'
                    
                song_info = {
                    'song_id': data[i]['id'],
                    'artist': [],
                    'song_name': data[i]['name'],
                    'album_name': album_name,
                    'mp3_url': url,
                    'quality': quality
                }
                if 'artist' in data[i]:
                    song_info['artist'] = data[i]['artist']
                elif 'artists' in data[i]:
                    for j in range(0, len(data[i]['artists'])):
                        song_info['artist'].append(data[i]['artists'][j]['name'])
                    song_info['artist'] = ', '.join(song_info['artist'])
                else:
                    song_info['artist'] = '未知艺术家'

                temp.append(song_info)

        elif dig_type == 'artists':
            temp = []
            for i in range(0, len(data)):
                artists_info = {
                    'artist_id': data[i]['id'],
                    'artists_name': data[i]['name'],
                    'alias': ''.join(data[i]['alias'])
                }
                temp.append(artists_info)

            return temp

        elif dig_type == 'albums':
            for i in range(0, len(data)):
                albums_info = {
                    'album_id': data[i]['id'],
                    'albums_name': data[i]['name'],
                    'artists_name': data[i]['artist']['name']
                }
                temp.append(albums_info)

        elif dig_type == 'top_playlists':
            for i in range(0, len(data)):
                playlists_info = {
                    'playlist_id': data[i]['id'],
                    'playlists_name': data[i]['name'],
                    'creator_name': data[i]['creator']['nickname']
                }
                temp.append(playlists_info)


        elif dig_type == 'channels':
            url, quality = geturl(data)
            channel_info = {
                'song_id': data['id'],
                'song_name': data['name'],
                'artist': data['artists'][0]['name'],
                'album_name': 'DJ节目',
                'mp3_url': url,
                'quality': quality
            }
            temp = channel_info

        elif dig_type == 'playlist_classes':
            soup = BeautifulSoup(data)
            dls = soup.select('dl.f-cb')
            for dl in dls:
                title = dl.dt.text
                sub = [item.text for item in dl.select('a')]
                temp.append(title)
                self.playlist_class_dict[title] = sub

        elif dig_type == 'playlist_class_detail':
            log.debug(data)
            temp = self.playlist_class_dict[data]

        return temp
