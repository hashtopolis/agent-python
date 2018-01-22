class HashcatStatus:
    def __init__(self, line):
        # parse
        self.status = -1
        self.speed = []
        self.exec_runtime = []
        self.curku = 0
        self.progress = [0, 0]
        self.rec_hash = [0, 0]
        self.rec_salt = [0, 0]
        self.rejected = 0

        line = line.split("\t")
        if line[0] != "STATUS":
            # invalid line
            return
        elif len(line) < 19:
            # invalid line
            return
        self.status = int(line[1])
        index = 3
        while line[index] != "EXEC_RUNTIME":
            self.speed.append([int(line[index]), int(line[index + 1])])
            index += 2
        while line[index] != "CURKU":
            index += 1
        self.curku = int(line[index + 1])
        self.progress[0] = int(line[index + 3])
        self.progress[1] = int(line[index + 4])
        self.rec_hash[0] = int(line[index + 6])
        self.rec_hash[1] = int(line[index + 7])
        self.rec_salt[0] = int(line[index + 9])
        self.rec_salt[1] = int(line[index + 10])
        self.rejected = int(line[index + 12])

    def is_valid(self):
        return self.status >= 0

    def get_progress(self):
        return self.progress[0]

    def get_state(self):
        return self.status - 1

    def get_curku(self):
        return self.curku

    def get_progress_total(self):
        return self.progress[1]

    def get_speed(self):
        total_speed = 0
        for s in self.speed:
            total_speed += int(float(s[0]) * 1000 / s[1])
        return total_speed

    def get_rejected(self):
        return self.rejected
