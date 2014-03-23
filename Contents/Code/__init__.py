from datetime import datetime
import time
import re

####################################################################################################

PLUGIN_PREFIX = "/video/9gagtv"

FEED = 'http://9gag.tv/api/index/LJEGX?%s&limit=24&direction=1&includeSelf=1'
YOUTUBE_VIDEO_PAGE = 'http://www.youtube.com/watch?v=%s'
YOUTUBE_VIDEO_FORMATS = ['Standard', 'Medium', 'High', '720p', '1080p']
YOUTUBE_FMT = [34, 18, 35, 22, 37]

NAME          = L('9Gag.TV')

# make sure to replace artwork with what you want
ART           = 'art-default.jpg'
ICON          = 'icon-default.png'

####################################################################################################

def Start():
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, Menu, NAME, ICON, ART)
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)
    VideoItem.thumb = R(ICON)
    
    HTTP.CacheTime = CACHE_1HOUR

def Menu():

    dir = MediaContainer(viewGroup="InfoList",title2=L('Episodes'), httpCookies=HTTP.CookiesForURL('http://www.youtube.com/'))
    dir = FeedMenu(feed = '') 
    return dir

def FeedMenu(feed=''):
    oc = ObjectContainer(title2=L('Episodes'), view_group='List')

    if (feed != ''):
		feed = 'refId=%s&' % feed 

    Log('FEEDING: %s' % feed)

    rawfeed = JSON.ObjectFromURL(FEED % feed, encoding='utf-8',cacheTime=CACHE_1HOUR)

    for video in rawfeed['data']['posts']:
        video_id = video['hashedId']
        title = video['title'] 
        video_url = '%s&%s' % (video['sourceUrl'],'hd=1')
        Log('URL video_url: %s' % video_url)

        if (video_id != None):
	      if video.has_key('description'):
		    summary = video['description']
	      duration = durationToSeconds( video['videoDuration'] );
	      rating = video['externalView']
	      published = video['publishTimestamp']
	      date = datetime.strptime(published,"%Y-%m-%d %H:%M:%S")

	      thumb = video['ogImageUrl']
	      oc.add(VideoClipObject(url=video_url, title=title, originally_available_at=date, summary=summary, thumb=Callback(Thumb, url=thumb)))
		  
    oc.add(NextPageObject(key=Callback(FeedMenu, feed=video_id), title='Mais...'))

    return oc
     
#		  dir.Append(Function(VideoItem(PlayVideo, title=title, subtitle=published, summary=summary, duration=duration, rating=rating, thumb=Function(Thumb, url=thumb)), video_id=video_id,video_url=video_url))
	
#    if len(dir) == 0:
#      return MessageContainer(L('Error'), L('This query did not return any result'))
#    else:
#      return dir

def Thumb(url):
  try:
    data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON))
    
def PlayVideo(sender, video_id, video_url):
  Log('URL DIN1: %s' % video_url)
  yt_page = HTTP.Request('%s' % video_url, cacheTime=1).content
#   yt_page = HTTP.Request(YOUTUBE_VIDEO_PAGE % (video_id), cacheTime=1).content
    
  fmt_url_map = re.findall('"url_encoded_fmt_stream_map".+?"([^"]+)', yt_page)[0]
  fmt_url_map = fmt_url_map.replace('\/', '/').split(',')

  fmts = []
  fmts_info = {}

  for f in fmt_url_map:
    map = {}
    params = f.split('\u0026')
    for p in params:
      (name, value) = p.split('=')
      map[name] = value
    quality = str(map['itag'])
    fmts_info[quality] = String.Unquote(map['url'])
    fmts.append(quality)

  index = YOUTUBE_VIDEO_FORMATS.index('720p')
  if YOUTUBE_FMT[index] in fmts:
    fmt = YOUTUBE_FMT[index]
  else:
    for i in reversed( range(0, index+1) ):
      if str(YOUTUBE_FMT[i]) in fmts:
        fmt = YOUTUBE_FMT[i]
        break
      else:
        fmt = 5

  url = (fmts_info[str(fmt)]).decode('unicode_escape')
  Log("  VIDEO URL --> " + url)
  return Redirect(url)

def durationToSeconds(duration):
	"""
	duration - ISO 8601 time format
	examples :
		'P1W2DT6H21M32S' - 1 week, 2 days, 6 hours, 21 mins, 32 secs,
		'PT7M15S' - 7 mins, 15 secs
	"""
#	Log('Duracao: %s' % duration)
	split   = duration.split('T')
	period  = split[0]
	time    = split[1]
	timeD   = {}

	# days & weeks
	if len(period) > 1:
		timeD['days']  = int(period[-2:-1])
	if len(period) > 3:
		timeD['weeks'] = int(period[:-3].replace('P', ''))

	# hours, minutes & seconds
	if len(time.split('H')) > 1:
		timeD['hours'] = int(time.split('H')[0])
		time = time.split('H')[1]
	if len(time.split('M')) > 1:
		timeD['minutes'] = int(time.split('M')[0])
		time = time.split('M')[1]    
	if len(time.split('S')) > 1:
		timeD['seconds'] = int(time.split('S')[0])

	# convert to seconds
	timeS = timeD.get('weeks', 0)   * (7*24*60*60) + \
			timeD.get('days', 0)    * (24*60*60) + \
			timeD.get('hours', 0)   * (60*60) + \
			timeD.get('minutes', 0) * (60) + \
			timeD.get('seconds', 0)

#	Log('Duracao: %s' % timeS)
	return timeS*1000