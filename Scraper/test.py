import requests

image_link = "https://i.imgur.com/2shdwke.jpg"
response = requests.get(image_link)
local_image_file = "abc as.jpg"
file = open(local_image_file, "wb")
file.write(response.content)
file.close()