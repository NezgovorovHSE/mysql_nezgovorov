E-commerce Database Project. The entire infrastructure is implemented using Docker.

Implemented:
1. Database: docker/mysql folder
2. Automatic database deployment via Docker Compose and data storage in a virtual volume: app/__pycache__ folders + docker-compose.yaml
3. Software implementation of a trigger in Python, later replaced by a built-in database trigger (marked with "old_" in the filename): app folder
4. Generation of master data and order generation using the trigger and existing database data: docker/python-app folder

Additional Materials:
1. Project structure, including screenshots of the database schema and Docker project structure: structure folder
2. Examples of SQL-queries on the populated database (screenshots): queries folder
3. Python performance tests checking the processing speed of SQL queries on a database with 2 million records (code + screenshots): testing folder

Prerequisites: Docker and Docker Compose installed

Deployment Instructions:
1. Clone the repository
       git clone https://github.com/NezgovorovHSE/mysql_nezgovorov.git
       cd mysql_nezgovorov
2. Run the container
        docker-compose up -d
