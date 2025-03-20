build:
	docker-compose up --build -d

run:
	docker-compose up -d

stop:
	docker-compose down

clean:
	docker system prune -af

attach:
	docker exec -it gstreamer_python bash	

reattach:
	docker-compose down
	docker-compose up -d
	docker exec -it gstreamer_python bash	

init: 
	make build
	make run
	make attach