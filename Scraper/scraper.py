from bs4 import BeautifulSoup as soup
from urllib.request import urlopen as uReq
import csv
import time
import random
import os
import re
import urllib
import requests










#-----------------#Scrape info from parent page or saved csv file to get list of makers and number of devices#-----------------#


def create_maker_list(makerlistdir):
	parent_url = 'https://www.gsmarena.com/makers.php3'

	uClient = uReq(parent_url)
	parent_page_html = uClient.read()
	uClient.close()

#scrape all brand names and number of devices
	parent_page = soup(parent_page_html, features="html.parser")
	brands = parent_page.findAll("td")

#init makerlist

	makerlist = [ [ "NA" for i in range(4) ] for brand in brands ] 
#MAX = 0
	i=0

	for brand in brands:
		makerlist[i][0] = i+1 #index
		makerlist[i][3] = brand.a["href"] #Link to Maker's list
		makerlist[i][2] = brand.a.span.text #No. of devices
		makerlist[i][1] = brand.a.text[:-len(makerlist[i][2])] #Maker name
		makerlist[i][2] = int(str(makerlist[i][2])[:-7])
	#	if MAX <= int(makerlist[i][2]):
	#			MAX = makerlist[i][2]
		i = i+1

	#print(MAX) #MAX = 1242, Thanks Samsung
	with open(makerlistdir, 'w', newline='') as csvfile:
		writer = csv.writer(csvfile)
		for row in makerlist:
			writer.writerow(row)

	return makerlist






def import_maker_list(makerlistdir):
	makerlist = []
	with open(makerlistdir, 'r', newline='') as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			makerlist.append(row)
	return makerlist













#-----------------#Scrape info from each manufacturer to get a list of all the devices#-----------------#


def get_device_list(makerlist,devicelistdir):
	device_list = [["Device index", "Manufacturer", "Device Name", "Link"]] # This will be our list of devices and links to their respective pages

#for maker in makerlist:
	device_index = 1

	for makers in makerlist:

		maker = makers[1]
		devices_url = 'https://www.gsmarena.com/'+str(makers[3])
		uClient = uReq(devices_url)
		devices_page_html = uClient.read()
		uClient.close()
		time.sleep(random.randrange(3,10)) #delay to not get banned

#check for more pages at the bottom since each page only displays about 40 devices

		pages_list = [devices_url]# This will hold a list of all the pages for the manufacturer
		devices_page = soup(devices_page_html, features="html.parser")
		pages = devices_page.findAll("div",{"class":"nav-pages"})
		pages = soup(str(pages), features="html.parser")
		pages = pages.findAll("a")
		for page in pages:
			pages_list.append("https://www.gsmarena.com/"+str(page["href"]))

			#print(pages_list)
#get a complete list of all devices and their links

		for link in pages_list:

#open each link
			devices_url = link
			uClient = uReq(devices_url)
			devices_page_html = uClient.read()
			uClient.close()
			time.sleep(random.randrange(3,10)) #delay to not get banned
			devices_page = soup(devices_page_html, features="html.parser")

#grab all the devices on the page
			devices = devices_page.findAll("ul",{"class" : ""})
			devices = devices[0]
			i = 0

			for device in devices:
				if i == 0:
					pass
				elif i == (len(devices)-1):
					pass
				else:
					entry = [device_index, maker, device.span.text, "https://www.gsmarena.com/"+str(device.a["href"])]
					device_list.append(entry)
					with open(devicelistdir, 'a+', newline='') as csvfile:
						writer = csv.writer(csvfile)
						writer.writerow(entry)
					device_index = device_index + 1
#					print("\n")
#					print(device.a["href"])
#					print(device.span.text)
#					print("\n")
#					print(device)
#					print("\n\n")
				i=i+1

	return device_list





def import_device_list(devicelistdir):
	device_list = []
	with open(devicelistdir, 'r', newline='') as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			device_list.append(row)
	return device_list















#-----------------#Scrape and organize all the info about each device that we need#-----------------#

def get_device_info(makerlist, device_list):

	total_devices = len(device_list)

	#define a function that grabs info from the html soup based on the "data-spec" key or fills "NA" if not available:

	def get_data(key):

		try:
			get_text_data = device_page.find("td",{"data-spec":key}).text
		except:
			get_text_data = "NA"

		return get_text_data


	#create a folder for each manufacturer


	for maker in makerlist:
		try:
			os.mkdir('data/'+maker[1])
		except:
			pass

	#create a folder for each device and get all the info in there
	for device in device_list:
		try:
			os.mkdir('data/'+device[1]+'/'+device[2])
		except:
			pass

		local_image_file = 'data/'+device[1]+'/'+device[2]+'/'+device[2]+'.jpg'
		#print(local_image_file)
		if os.path.exists(local_image_file):
			print("Ignored "+device[1]+" "+device[2])
			#file already exists! Do nothing Currently, the check is done using just the image file. Maybe check the data file too in future?
			pass

		else:


# First download and save device image

			device_url = device[3]

			uClient = uReq(device_url)
			device_page_html = uClient.read()
			uClient.close()
			device_page = soup(device_page_html, features="html.parser")
			time.sleep(random.randrange(3,10)) #delay to not get banned

			raw_image_link = device_page.find("style",{"type":"text/css"})
			try:
				#use re to clean image link
				raw_image_link = str(raw_image_link)
				pattern = re.search("url[(].*jpg [)]", raw_image_link)
				#print("pattern = "+str(pattern))
				found = pattern[0] #There may be a bug here worth fixing, but it is unlikely there will be more than one urls
				#print("found = "+found)
				image_link = found[5:-2]
				#print("image link = "+image_link)
			#download the image and save it to the directory
				response = requests.get(image_link)
				file = open(local_image_file, "wb")
				file.write(response.content)
				file.close()
				time.sleep(random.randrange(3,10)) #delay to not get banned

			except:
				with open('data/noimage.csv', 'a+', newline='') as csvfile:
					writer = csv.writer(csvfile)
					writer.writerow(device)


#then scrape all relevent device info

			deviceinfo = ["" for x in range(21)]
			deviceinfo[0] = get_data("status")
			deviceinfo[1] = get_data("os")
			deviceinfo[2] = get_data("dimensions")
			deviceinfo[3] = get_data("weight")
			deviceinfo[4] = get_data("displaysize")
			deviceinfo[5] = get_data("displayresolution")
			deviceinfo[6] = get_data("displaytype")
			deviceinfo[7] = get_data("batdescription1")
			deviceinfo[8] = get_data("chipset")
			deviceinfo[9] = get_data("cpu")
			deviceinfo[10] = get_data("gpu")
			deviceinfo[11] = get_data("internalmemory")
			deviceinfo[12] = get_data("memoryslot")
			deviceinfo[13] = get_data("cam1modules")
			deviceinfo[14] = get_data("cam2modules")
			deviceinfo[15] = get_data("cam3modules")
			deviceinfo[16] = get_data("cam4modules")
			deviceinfo[17] = get_data("cam5modules")
			deviceinfo[18] = get_data("cam6modules")
			deviceinfo[19] = get_data("cam7modules")
			deviceinfo[19] = get_data("cam8modules")
			deviceinfo[20] = get_data("cam9modules")

			Labels = ["Release Date", "OS", "Dimensions", "Weight", "Display Size", "Resolution", "Display Type", "Battery", "Chipset", "CPU", "GPU", "Internal Memory", "External Memory", "Cam1", "Cam2", "Cam3", "Cam4", "Cam5", "Cam6", "Cam7", "Cam8", "Cam9"]
			data_directory = 'data/'+device[1]+'/'+device[2]+'/'+device[2]+'.csv'
			with open (data_directory ,'w') as csvfile:
				writer = csv.writer(csvfile)
				writer.writerow(Labels)
				writer.writerow(deviceinfo)

		# Report on percentage completion

		devices_done = int(device[0])
		percentage_completion = (devices_done/total_devices)*100
		print(str(devices_done)+' out of '+str(total_devices)+' done! Percentage completion: '+str(percentage_completion))



"""

			print('\n\n\n')
			print('rd:'+device_release_date+'\nos:'+device_os+'\nsize:'+device_size+device_mass+'\ndisplay:'+device_display_size+device_display_type+device_resolution+'\ngpu:'+device_graphics+'\nbattery:'+device_battery+'\nMemory:'+device_memory_int+device_memory_ext+'\ncameras:'+device_cam1+device_cam2+device_cam3+device_cam4+device_cam5+device_cam6+device_cam7+device_cam8+device_cam9)

"""







#--------------------------------------------#Main Program#--------------------------------------------#

def main():
	makerlistdir = 'data/makerlist.csv'
	devicelistdir = 'data/devices.csv'
	#makerlist = create_maker_list(makerlistdir)
	makerlist = import_maker_list(makerlistdir)
	#device_list = get_device_list(makerlist, devicelistdir)
	device_list = import_device_list(devicelistdir)
	get_device_info(makerlist, device_list)

main()