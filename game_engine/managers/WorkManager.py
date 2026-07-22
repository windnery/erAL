from random import randint

class WorkManager:
    def __init__(self):
        self.works: int = randint(1000, 1200)
        self.works_done: int = 0

    def set_works(self):
        # 设置工作量
        works = randint(1000, 1200)
        self.works = works

    def do_work(self, works: int):
        # 做工作
        if self.works < works:
            self.works_done += self.works
            self.works = 0
        else:
            self.works -= works
            self.works_done += works