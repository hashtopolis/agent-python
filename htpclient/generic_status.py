class GenericStatus:
    def __init__(self, line):
        # parse
        self.valid = False
        self.speed = 0
        self.progress = 0

        line = line.split(" ")
        if line[0] != "STATUS":
            # invalid line
            return
        elif len(line) != 3:
            # invalid line
            return
        self.progress = int(line[1])
        self.speed = int(line[2])
        self.valid = True

    def is_valid(self):
        return self.valid

    def get_progress(self):
        return self.progress

    def get_speed(self):
        return self.speed
