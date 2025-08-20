# Rick and Morty
Django REST API for managing Rick & Morty characters with background synchronization from external API.

### Technologies to use
- Public API: https://rickandmortyapi.com/documentation/
- Use Celery as task scheduler for data synchronization for Rick & Morty API
- Python, Django, ORM, PostgreSQL, Git
- All endpoints should be documented via Swagger

### How to run
- Copy .env.sample to .env and populate
- `docer-compose up --build`
- Create admin user & Create schedule for running sync in db
