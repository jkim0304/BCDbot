run:
	sudo ./bcdserver > bcdserver.log &
	python3 bot.py > bot.log & 

server: 
	go build bcdserver.go

images:
	python3 generate_clump_data.py

install: 
	sudo yum -y install python3
	sudo yum -y install golang
	sudo yum -y install python3-pip
	sudo yes | pip3 install pillow
	sudo yes | pip3 install discord.py
	sudo yes | pip3 install gspread
	sudo yes | pip3 install oauth2client
	mkdir images