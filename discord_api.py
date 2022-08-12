import requests
import yaml


class DiscordAPI:
    def __init__(self, invite_code):
        self.server_data = self.get_server_data(invite_code)
        self.serverId = self.server_data['guild']['id']
        self.num_members = self.server_data['approximate_member_count']
        self.num_active = self.server_data['approximate_presence_count']
        self.server_name = self.server_data['guild']['name']

    def get_server_data(self, invite_code):
        api_url = f"https://discord.com/api/v9/invites/{invite_code}?with_counts=true&with_expiration=true"
        response = requests.get(api_url).json()
        return response
