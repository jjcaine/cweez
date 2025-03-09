import requests

url = "https://v1.basketball.api-sports.io/leagues"
headers = {
    'x-rapidapi-host': "v1.basketball.api-sports.io",
    'x-rapidapi-key': "38be905fa017cb31f10ea33f3e1b4483"
}
params = {
    'name': 'NCAA'
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

print(data)
