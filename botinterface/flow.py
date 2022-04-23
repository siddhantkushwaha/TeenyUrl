from datetime import datetime

"""
    Maintains current interaction with a user
"""


class Flow:

    def __init__(self, user_id, flow_type, expected_keys):
        self.timestamp = datetime.now()

        self.user_id = user_id
        self.type = flow_type
        self.expected_keys = expected_keys

        self.next_key = None

        self.keys = {}

    def is_old(self):
        return (datetime.now() - self.timestamp).total_seconds() >= 3600
