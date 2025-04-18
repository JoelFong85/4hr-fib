## Run these commands to install / run locally:

Activate python env:

```python -m venv venv```

```source venv/bin/activate```

Install dependencies:

```pip install -r requirements.txt```

python-dotenv[cli] package will be installed 

You can then run script with the main function you require:

```dotenv run -- python strategies/four_hr/main.py```

## Serverless

Run this to deploy serverless project. Ensure docker desktop is running first as it is required to install packages to create the zip file for deployment:

```sls deploy```

To check if lambdas are working, view the lambda in aws console, and check the monitor tab for cloudwatch logs. 