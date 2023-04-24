# Flask Project README

This is a Flask project that requires specific installation requirements and a virtual environment to run. Below are the instructions to set up the project on your local machine.

## Cloning the Repository

1. Clone the project repository by running the following command:

```
git clone https://github.com/vovann2003/business_product_project.git
```

2. Navigate to the project directory:

```
cd <repository>
```

## Prerequisites

Before proceeding, please make sure you have the following:

- Python 3.7 or higher installed on your system
- pip package installer for Python

## Virtual Environment Setup

1. Create a new virtual environment by running the following command:

```
python3 -m venv venv
```

2. Activate the virtual environment:

```
source venv/bin/activate (macOS/Linux)
venv\Scripts\activate (Windows)
```

## Installing Required Packages

1. Make sure your virtual environment is activated
2. Install the required packages using the following command:

```
pip install -r requirements.txt
```

## Running the Application

1. Make sure your virtual environment is activated
2. Set the `FLASK_APP` environment variable:

```
export FLASK_APP=app.py (macOS/Linux)
set FLASK_APP=app.py (Windows)
```

3. Set the `FLASK_ENV` environment variable:

```
export FLASK_ENV=development (macOS/Linux)
set FLASK_ENV=development (Windows)
```

4. Run the Flask application:

```
flask run
```

5. Open your web browser and go to `http://localhost:5000` to see the running application.

## Stopping the Application

To stop the Flask application, press `Ctrl + C` in the terminal window where the server is running. Then deactivate the virtual environment:

```
deactivate
``` 

Congratulations, you have successfully installed and run the Flask application!