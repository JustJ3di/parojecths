class Increment:
    i = 0
    def __init__(self):
        self.i = self.i
    def increment(self):
        self.i +=1
    def get_i(self):
        return self.i


count = Increment()
count.increment()
count.increment()
a = count.get_i()
print(a)