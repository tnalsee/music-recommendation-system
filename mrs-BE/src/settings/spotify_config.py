# Spotify Keys
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
CLIENT_ID = config['SPOTIFY']['CLIENT_ID']
CLIENT_KEY = config['SPOTIFY']['CLIENT_KEY']
