import abc

class Person():
    def __init__(self, id, name, party, constituency, region):
        self.id = id
        self.name = name
        self.party = party
        self.constituency = constituency
        self.votes = []
        self.region = region

class MP(Person):
    def describe_mp(self):
        description = f"Hello, I am {self.name} of the {self.party} party, representing the constituents of {self.constituency}"
        print(description)