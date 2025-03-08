## Steps to run project with the traditional method

# este es un ejemplo, ir complementando

1. Clone the repo
    ```sh
        git clone https://github.com/JoaquiinAguilar/API-REST-PERSONAS.git
    ```
2. Access into the folder 
    `cd personas_proyecto`
3. Create an virtual environment 
    `python -m venv .env`
4. Activate the virtual environment 
    If you're using MacOs, Linux or any UNIX environment this command will work
    `source .env/bin/activate`

    If you are in a Windows Machine This command is necessary to make it work
    `.env\Scripts\Activate.bat`
5. Update pip to latests version
    `pip install --upgrade pip`
6. Install libraries
    `pip install -r requirements.txt --no-cache`
7. Create file .env inside **** folder, copy the content from **.env.example** and change the database connection values
8. Run migrations: `python manage.py makemigrations`
                   `python manage.py migrate`
9. Execute python project
    `python manage.py runserver`
10. Go to the explorer and navigate to `http://127.0.0.1:8000/`
11. Ready to go!
