import os
from googleapiclient.discovery import build
import re
from pymongo import MongoClient
from datetime import timedelta, datetime
import mysql.connector

youtube_api_key = os.environ.get('YT_API_KEY')
user_MySQL = os.environ.get('MYSQL_USER')
passwd_MySQL = os.environ.get('MYSQL_PASSWORD')

youtube = build('youtube','v3', developerKey=youtube_api_key)


connection = MongoClient('localhost', 27017)
db = connection.youtube


conn = mysql.connector.connect(
			host = 'localhost',
			user = user_MySQL,
			passwd = passwd_MySQL,
			database = 'youtube'
			)

cur = conn.cursor()



cur.execute('CREATE TABLE IF NOT EXISTS channels (id   int PRIMARY KEY AUTO_INCREMENT UNIQUE,\
				chanelTitle   VARCHAR(150),\
				videoCount int,\
				viewCount int,\
				subscriberCount int,\
				TotalPlaylists int,\
				chanelcountry VARCHAR(5),\
				channelId VARCHAR(50) UNIQUE)')



cur.execute('CREATE TABLE IF NOT EXISTS playlists (id   int PRIMARY KEY AUTO_INCREMENT UNIQUE,\
				playlistTitle   VARCHAR(150),\
				playlistPublish DATETIME,\
				channelId int,\
				TotalVideos int,\
				duration TIME,\
				playlistId VARCHAR(50) UNIQUE)')



cur.execute('CREATE TABLE IF NOT EXISTS videos (id   int PRIMARY KEY AUTO_INCREMENT UNIQUE,\
				videoTitle   VARCHAR(150),\
				publishedAt DATETIME,\
				playlistId int,\
				viewCount int,\
				likeCount int,\
				dislikeCount int,\
				commentCount int,\
				duration TIME,\
				videoId VARCHAR(50) UNIQUE)')



cur.execute('CREATE TABLE IF NOT EXISTS comments (id   int PRIMARY KEY AUTO_INCREMENT UNIQUE,\
				authorComment   VARCHAR(150),\
				authorChannelId   VARCHAR(50),\
				likeCount int,\
				totalReplyCount int,\
				publishedAt DATETIME,\
				videoId int,\
				commentId VARCHAR(50) UNIQUE)')



class Helper:
	def __init__(self):
		pass

	def title_to_underscore_title(self,title:str):
		title = re.sub(r'[\W_]+', "_", title)
		return title.lower()

helper = Helper()

f = "%Y-%m-%dT%H:%M:%S"

def get_channelId():
	user_option = input('Insira a URL do Canal da busca:')
	user_option = re.findall(r'([^/]+$)',user_option)

	return user_option 


def get_channel():
	get_channel_id = get_channelId()
	request = youtube.channels().list(
					part='statistics, brandingSettings',
					id=get_channel_id
					)

	response = request.execute()

	collection = db.channels

	upsert_channel = "INSERT INTO channels \
								(chanelTitle, videoCount, viewCount, subscriberCount, chanelcountry, channelId)\
								VALUES ( %s, %s, %s, %s, %s, %s)\
								ON DUPLICATE KEY UPDATE \
								chanelTitle = chanelTitle, videoCount = videoCount, viewCount = viewCount, subscriberCount = subscriberCount,\
								chanelcountry = chanelcountry"


	channel_zip_id = list()
	for item in response['items']:
		channelId = item['id']
		viewCount = item['statistics']['viewCount']
		subscriberCount = item['statistics']['subscriberCount']
		videoCount = item['statistics']['videoCount']
		chanelTitle = item['brandingSettings']['channel']['title']
		chanelDescription = item['brandingSettings']['channel']['description']
		chanelcountry = item['brandingSettings']['channel'].get('country',None)

		channel_insert = (chanelTitle, videoCount, viewCount, subscriberCount, chanelcountry, channelId)


		cur.execute(upsert_channel,channel_insert)
		last_row_id = cur.lastrowid
		if last_row_id == 0:
			cur.execute('SELECT id FROM channels WHERE channelId = %s',(channelId,))
			last_row_id = cur.fetchone()[0]

		channel_NoSQL ={
							'channelId': channelId,
							'channelId_SQL':last_row_id,
							'chanelDescription':chanelDescription
						}

		channel_mongo = collection.replace_one({"channelId": channelId}, channel_NoSQL, upsert=True)

		tuple_id = channelId, last_row_id
		channel_zip_id.append(tuple_id)


	conn.commit()
	return channel_zip_id


def get_playlistId():

	channelId_tuple = get_channel()
	channelId = channelId_tuple[0][0]

	playlist_zip_id = list()

	nextPageToken = None
	collection = db.playlists



	upsert_playlist = "INSERT INTO playlists \
						(playlistTitle, playlistPublish, channelId, playlistId) \
						VALUES ( %s, %s, %s, %s)\
						ON DUPLICATE KEY UPDATE \
						playlistTitle = playlistTitle, playlistPublish = playlistPublish, channelId = channelId"

	while True:
		pl_request = youtube.playlists().list(
						part='contentDetails, snippet',
						channelId=channelId,
						maxResults=50,
						pageToken = nextPageToken
						)

		pl_response = pl_request.execute()
		
		total_platlists = 0

		for item in pl_response['items']:
			playlist_id = item['id']
			playlist_title = helper.title_to_underscore_title(item['snippet']['title'])
			playlist_description = item['snippet']['description']

			playlist_publish = item['snippet']['publishedAt'].split('Z')[0]
			playlist_publish = datetime.strptime(playlist_publish,f)

			playlist_insert = (playlist_title, playlist_publish, channelId_tuple[0][1], playlist_id)

			cur.execute(upsert_playlist, playlist_insert)
			last_row_id = cur.lastrowid
			if last_row_id == 0:
				cur.execute('SELECT id FROM playlists WHERE playlistId = %s',(playlist_id,))
				last_row_id = cur.fetchone()[0]

			playlist_NoSQL ={
								'playlistId': playlist_id,
								'playlistId_SQL':last_row_id,
								'playlist_description':playlist_description
							}

			playlist_mongo = collection.replace_one({"playlistId": playlist_id}, playlist_NoSQL, upsert=True)

			tuple_id = playlist_id, last_row_id
			playlist_zip_id.append(tuple_id)

			total_platlists += 1


			cur.execute('UPDATE channels SET TotalPlaylists = %s WHERE id = %s', (total_platlists, channelId_tuple[0][1]))

		nextPageToken = pl_response.get('nextPageToken')
		if not nextPageToken:
			break

	conn.commit()

	return playlist_zip_id

def get_videos():

	videos_zip_id = list()


	hours_pattern = re.compile(r'(\d+)H')
	minutes_pattern = re.compile(r'(\d+)M')
	seconds_pattern = re.compile(r'(\d+)S')

	list_playlistId = get_playlistId()

	collection = db.videos

	upsert_videos = "INSERT INTO videos \
						(videoTitle, publishedAt, playlistId, viewCount, likeCount, dislikeCount, commentCount, duration, videoId)\
						VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s)\
						ON DUPLICATE KEY UPDATE \
						videoTitle = videoTitle, publishedAt = publishedAt, playlistId = playlistId, viewCount = viewCount, likeCount = likeCount,\
						dislikeCount = dislikeCount, commentCount = commentCount, duration = duration"


	for play, playId_SQL in list_playlistId:

		nextPageToken = None

		while True:
			pl_request_items = youtube.playlistItems().list(
							part='contentDetails, snippet',
							playlistId=play,
							maxResults=50,
							pageToken = nextPageToken
							)

			pl_response_items = pl_request_items.execute()

			vid_ids = list()

			for item in pl_response_items['items']:
				vid_ids.append(item['contentDetails']['videoId'])

			vid_request = youtube.videos().list(
							part='statistics, snippet, contentDetails',
							id=','.join(vid_ids)
							)

			vid_response = vid_request.execute()

			total_seconds = 0
			total_vids = 0

			for item in vid_response['items']:
				vid_title = helper.title_to_underscore_title(item['snippet']['title'])
				vid_id = item['id']
				viewCount = item['statistics']['viewCount']
				likeCount = item['statistics']['likeCount']
				dislikeCount = item['statistics']['dislikeCount']
				commentCount = item['statistics']['commentCount']
				duration = item['contentDetails']['duration']
				video_description = item['snippet']['description']

				publishedAt = item['snippet']['publishedAt'].split('Z')[0]
				publishedAt = datetime.strptime(publishedAt,f)

				hours = hours_pattern.search(duration)
				minutes = minutes_pattern.search(duration)
				seconds = seconds_pattern.search(duration)

				hours = int(hours.group(1)) if hours else 0
				minutes = int(minutes.group(1)) if minutes else 0
				seconds = int(seconds.group(1)) if seconds else 0

				duration = f'{hours}:{minutes}:{seconds}'


				video_seconds = timedelta(
									hours = hours,
									minutes = minutes,
									seconds = seconds
									).total_seconds()

				total_seconds += video_seconds

				video_insert = (vid_title, publishedAt, playId_SQL, viewCount, likeCount, dislikeCount, commentCount, duration, vid_id)
				cur.execute(upsert_videos,video_insert)
				last_row_id = cur.lastrowid
				if last_row_id == 0:
					cur.execute('SELECT id FROM videos WHERE videoId = %s',(vid_id,))
					last_row_id = cur.fetchone()[0]

				videos_NoSQL={
									'videoId': vid_id,
									'videoId_SQL': last_row_id,
									'video_description':video_description
								}


				tuple_id = vid_id, last_row_id
				videos_zip_id.append(tuple_id)
					
				videos_mongo = collection.replace_one({'videoId': vid_id}, videos_NoSQL, upsert=True)

			nextPageToken = pl_response_items.get('nextPageToken')

			total_seconds = int(total_seconds)

			minutes, seconds = divmod(total_seconds, 60)
			hours, minutes = divmod(minutes, 60)

			playlist_duration = f'{hours}:{minutes}:{seconds}'
			total_vids += 1

			cur.execute('UPDATE playlists SET duration = %s, TotalVideos = %s WHERE id = %s', (playlist_duration, total_vids, playId_SQL))

			if not nextPageToken:
				break

	conn.commit()
	return videos_zip_id


def get_comment_videos():

	list_videosId = get_videos()

	collection = db.comments

	upsert_comments = "INSERT INTO comments \
					(authorComment, authorChannelId, likeCount, totalReplyCount, publishedAt, videoId, commentId)\
					VALUES ( %s, %s, %s, %s, %s, %s, %s)\
					ON DUPLICATE KEY UPDATE \
					authorComment = authorComment, authorChannelId = authorChannelId, likeCount = likeCount, totalReplyCount = totalReplyCount,\
					publishedAt = publishedAt, videoId = videoId"

	for vid, vidId_SQL in list_videosId:

		comment_request = youtube.commentThreads().list(
						part='snippet',
						videoId=vid,
						maxResults=50,
						)

		comment_response = comment_request.execute()

		for item in comment_response['items']:
			comment_id = item['id']
			comment = item['snippet']['topLevelComment']['snippet']['textOriginal']
			author_comment = item['snippet']['topLevelComment']['snippet'].get('authorDisplayName',None)
			author_channel_id = item['snippet']['topLevelComment']['snippet']['authorChannelId'].get('value',None)
			likeCount = item['snippet']['topLevelComment']['snippet'].get('likeCount',0)
			totalReplyCount = item['snippet'].get('totalReplyCount',0)

			publishedAt = item['snippet']['topLevelComment']['snippet']['publishedAt'].split('Z')[0]
			publishedAt = datetime.strptime(publishedAt,f)

			coment_insert = (author_comment, author_channel_id, likeCount, totalReplyCount, publishedAt, vidId_SQL, comment_id)

			cur.execute(upsert_comments,coment_insert)
			last_row_id = cur.lastrowid
			if last_row_id == 0:
				cur.execute('SELECT id FROM comments WHERE commentId = %s',(comment_id,))
				last_row_id = cur.fetchone()[0]

			comments_NoSQL={
								'commentId': comment_id,
								'commentId_SQL': last_row_id,
								'comment_description': comment
							}

			comments_mongo = collection.replace_one({'commentId': comment_id}, comments_NoSQL, upsert=True)

	conn.commit()
	conn.close()
	return print('Atualização realizada com Sucesso!!')


get_comment_videos()