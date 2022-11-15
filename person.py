import abc

class Person():
    def __init__(self, name, party, constituency):
        self.name = name
        self.party = party
        self.constituency = constituency

class MP(Person):
    def describe_mp(self):
        description = f"Hello, I am {self.name} of the {self.party} party, representing the constituents of {self.constituency}"
        if self.party == "Conservative":
            description += " and I'm a CUNT"
        print(description)