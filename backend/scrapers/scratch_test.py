import urllib.request
import re
html = urllib.request.urlopen('https://news.google.com/rss/articles/CBMiggFBVV95cUxNNjBnTlU0YTZYZDZDYktURXFWSzJrTkpEZXpIelhRMXZHdEJHUFpVZWxkcWh5cmp4VnJtdEliUDk5X3NCcVQySGhuOHF0MjUtTV9wNkZzNVFTb1VabWVkNkI4S0tGeHFCeGQ5ZHJVZTlBWFVXQUp1bG5vUk1iWHIwSkJn?oc=5').read().decode('utf-8')
print([s for s in re.findall(r'https?://[^\s\"\'<]+', html) if 'google' not in s and 'gstatic' not in s])
