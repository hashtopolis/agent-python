class HashcatStatus:
    """Class to parse hashcat status output"""

    def __init__(self, raw_line: str):
        # parse
        raw_line = raw_line.strip()
        self.status = -1
        self.speed: list[tuple[int, int]] = []
        self.curku = 0
        self.progress = [0, 0]
        self.rec_hash = [0, 0]
        self.rec_salt = [0, 0]
        self.rejected = 0
        self.util: list[int] = []
        self.temp: list[int] = []

        line = raw_line.split("\t")

        if line[0] != "STATUS" or len(line) < 19:
            # invalid line
            return

        self.status = int(line[1])
        index = 3
        while line[index] != "EXEC_RUNTIME":
            self.speed.append((int(line[index]), int(line[index + 1])))
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
        if line[index + 11] == "TEMP":
            # we have temp values
            index += 12
            while line[index] != "REJECTED":
                self.temp.append(int(line[index]))
                index += 1
        else:
            index += 11
        self.rejected = int(line[index + 1])
        if len(line) > index + 2:
            index += 2
            if line[index] == "UTIL":
                index += 1
                while len(line) - 1 > index:  # -1 because the \r\n is also included in the split
                    self.util.append(int(line[index]))
                    index += 1

    def is_valid(self):
        """Check if the status is valid"""
        return self.status >= 0

    def get_progress(self):
        """Get the progress"""
        return self.progress[0]

    def get_state(self):
        """Get the state"""
        return self.status - 1

    def get_curku(self):
        """Get the current keyspace"""
        return self.curku

    def get_temps(self):
        """Get the temperatures"""
        return self.temp

    def get_progress_total(self):
        """Get the total progress"""
        return self.progress[1]

    def get_all_util(self):
        """Get all the util values"""
        return self.util

    def get_util(self):
        """Get the average util value"""
        if not self.util:
            return -1
        util_sum = 0
        for u in self.util:
            util_sum += u
        return int(util_sum / len(self.util))

    def get_speed(self):
        """Get the speed"""
        total_speed = 0
        for s in self.speed:
            total_speed += int(float(s[0]) * 1000 / s[1])
        return total_speed

    def get_rejected(self):
        """Get the rejected hashes"""
        return self.rejected
