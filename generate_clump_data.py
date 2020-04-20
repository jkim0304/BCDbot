from PIL import Image
import ssl
import urllib.request
import utils
import math
import time
ssl._create_default_https_context = ssl._create_unverified_context

ci = utils.getCardIndex()
arg = "Modern Horizons"
clumpscores = utils.getClumpScores()

for arg in clumpscores:

	legacy_unbans = clumpscores[arg]['legacy_unbans']
	top_cards = clumpscores[arg]['top_cards']
	clumps = clumpscores[arg]['clumps']


	card_list = list(legacy_unbans)
	for card in top_cards:
	    if card not in card_list:
	        card_list.append(card)

	# Sorted
	for clump in clumps:
	    for card in clump[0]:
	        if card not in card_list:
	            card_list.append(card)
	if len(card_list) == 0:
		continue
		
	images = list()
	for name in card_list:
		url  = ci[name]['art']
		req = urllib.request.Request(url)
		resp = urllib.request.urlopen(req)
		images.append(Image.open(resp))
		time.sleep(0.1)


	widths, heights = zip(*(i.size for i in images))

	total_width = sum(widths)
	total_height = heights[0]*math.ceil(len(widths)/4)

	new_im = Image.new('RGB', (total_width, total_height))

	x_offset = 0
	y_offset = 0
	i = 0
	print(len(widths))
	for im in images:
		i += 1
		new_im.paste(im, (x_offset,y_offset))
		x_offset += im.size[0]
		if i % 4 == 0:
	  		y_offset += im.size[1]
	  		x_offset = 0
	  	
	new_im.save("images/" + utils.encode_setname(arg)+".jpg")