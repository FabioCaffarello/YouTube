import os
from pytube import YouTube
import json
import re
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import concurrent.futures

api_key = os.environ.get('YT_API_KEY')

youtube = build('youtube','v3', developerKey=api_key)

##(CANAL: Pretty Printed | PLAYLIST: Flask SQLAlchemy >> Exemplo ilustrativo)
playlist_id = 'PLXmMXHVSvS-BlLA5beNJojJLlpE0PJgCW'
channelId='UC-QDfvrRIDB6F0bIO4I4HkQ'

class Helper:
	def __init__(self):
		pass

	def title_to_underscore_title(self,title:str):
		title = re.sub(r'[\W_]+', "_", title)
		return title.lower()

helper = Helper()


hours_pattern = re.compile(r'(\d+)H')
minutes_pattern = re.compile(r'(\d+)M')
seconds_pattern = re.compile(r'(\d+)S')

total_seconds = 0

f = "%Y-%m-%dT%H:%M:%S"

videos = []

nextPageToken = None
while True:
	pl_request = youtube.playlistItems().list(
				part='contentDetails, snippet',
				playlistId=playlist_id,
				maxResults=50,
				pageToken = nextPageToken
		)

	pl_response = pl_request.execute()

	vid_ids = []
	for item in pl_response['items']:
		vid_ids.append(item['contentDetails']['videoId'])

	vid_request = youtube.videos().list(
			part='statistics, snippet, contentDetails',
			id=','.join(vid_ids)
		)

	vid_response = vid_request.execute()

	for item in vid_response['items']:
		vid_title = item['snippet']['title']
		vid_id = item['id']
		description = item['snippet']['description']
		publishedAt = item['snippet']['publishedAt']
		channelTitle = item['snippet']['channelTitle']
		viewCount = item['statistics']['viewCount']
		likeCount = item['statistics']['likeCount']
		dislikeCount = item['statistics']['dislikeCount']
		commentCount = item['statistics']['commentCount']
		duration = item['contentDetails']['duration']


		hours = hours_pattern.search(duration)
		minutes = minutes_pattern.search(duration)
		seconds = seconds_pattern.search(duration)

		hours = int(hours.group(1)) if hours else 0
		minutes = int(minutes.group(1)) if minutes else 0
		seconds = int(seconds.group(1)) if seconds else 0


		video_seconds = timedelta(
			hours = hours,
			minutes = minutes,
			seconds = seconds
			).total_seconds()

		total_seconds += video_seconds

		videos.append(
			{
				'title': str(vid_title),
				'id': vid_id,
				'description': description,
				'publishedAt': publishedAt,
				'channelTitle': str(channelTitle),
				'viewCount': int(viewCount),
				'likeCount': int(likeCount),
				'dislikeCount': int(dislikeCount),
				'commentCount': int(commentCount),
			}	
		)
		
	nextPageToken = pl_response.get('nextPageToken')

	if not nextPageToken:
		break

total_seconds = int(total_seconds)

minutes, seconds = divmod(total_seconds, 60)
hours, minutes = divmod(minutes, 60)

duration = f'{hours}:{minutes}:{seconds}'

pl_info_request = youtube.playlists().list(
			part='contentDetails, snippet',
			channelId=channelId,
			maxResults=50
	)

pl_info_response = pl_info_request.execute()

play_lists =[]
for item in pl_info_response['items']:
	pl_title = item['snippet']['title']
	pl_id = item['id']
	play_lists.append(
		{
			'pl_title': pl_title,
			'pl_id': pl_id
		}	
	)

pl_name = []
for play in play_lists:
	play_title = play['pl_title'] if play['pl_id'] == playlist_id else None
	pl_name.append(play_title)
play_title = list(filter(lambda x: x != None, pl_name))[0]
play_title = helper.title_to_underscore_title(play_title)

os.mkdir(play_title)
os.makedirs(f'{play_title}/Textos')
os.makedirs(f'{play_title}/Videos')

path_video = f'{play_title}/Videos'

info_playlist = f'{play_title} \n Duração: \t {duration}'

with open(f'{play_title}/Textos/01-{play_title}.txt','w', encoding='utf-8') as file:
	file.write(info_playlist)


def donwload_videos(video):
	title = helper.title_to_underscore_title(video['title'])
	video_id = video['id']
	description = video['description']
	publishedAt = video['publishedAt']
	publishedAt = publishedAt.split('Z')[0]
	publishedAt = datetime.strptime(publishedAt, f)
	channelTitle = video['channelTitle']
	viewCount = video['viewCount']
	likeCount = video['likeCount']
	dislikeCount = video['dislikeCount']
	commentCount = video['commentCount']

	yt_link= f'https://youtu.be/{video_id}'

	text = f'{title} \n\n Canal: {channelTitle} \n link: {yt_link} \n Publicado em: {publishedAt} \n Número de Visualizações: {viewCount} \n Número de Likes: {likeCount} \t Númere de Dislikes: {dislikeCount} \t Número de comentários: {commentCount} \n\n Descrição: \n {description}'

	with open(f'{play_title}/Textos/{title}.txt','w', encoding='utf-8') as file:
		file.write(text)

	YouTube(yt_link).streams.first().download(output_path=path_video, filename=title)

with concurrent.futures.ThreadPoolExecutor() as executor:
	executor.map(donwload_videos, videos)
