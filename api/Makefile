.PHONY : bootstrap-api up down makemigrations migrate build generate_dashboard_routes shell

up:
	docker-compose up -d
down:
	docker-compose down --remove-orphans
bootstrap: build
	docker-compose down --volumes --remove-orphans
	docker-compose run --rm api bash entrypoint/bootstrap.sh
	make up
makemigrations:
	docker-compose exec api python manage.py makemigrations ${ARGS}
sqlmigrate:
	docker-compose exec api python manage.py sqlmigrate ${ARGS}
dbshell:
	docker-compose exec api python manage.py dbshell ${ARGS}
migrate:
	docker-compose exec api python manage.py migrate ${ARGS}
test:
	docker-compose exec api pytest --ds=settings.test ${ARGS}
build:
	docker-compose build
mypy:
	docker-compose exec api mypy .
dumpdata:
	docker-compose exec api python manage.py dumpdata ${MODEL_NAME}  --indent 4 > ./fixtures/${MODEL_NAME}.json
rebuild_index:
	docker-compose exec api python manage.py rebuild_index --noinput
generate_dashboard_routes:
	. ./generate_dashboard_routes.sh
shell:
	docker-compose exec api python manage.py shell_plus ${ARGS}