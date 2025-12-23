class HashcatStatus:
    def __init__(self, line):
        """
        Initializes the HashcatStatus object by parsing a machine-readable
        status line from Hashcat.

        Args:
            line (str): A single line of Hashcat machine-readable status
                        output.
        """
        self.status = -1
        self.speed = []
        self.exec_runtime = []
        self.curku = 0
        self.progress = [0, 0]
        self.rec_hash = [0, 0]
        self.rec_salt = [0, 0]
        self.rejected = 0
        self.util = []
        self.temp = []
        self.power = []
        self.unknown_fields = False

        try:
            fields = line.strip().split('\t')
            if not fields or fields[0] != 'STATUS':
                # Not a valid status line
                return

            self.status = int(fields[1])

            i = 2
            while i < len(fields):
                key = fields[i]
                i += 1

                if key == 'SPEED':
                    # Speed has two values per device: hashes over period and period in ms
                    while i + 1 < len(fields) and fields[i].isdigit() and fields[i+1].isdigit():
                        self.speed.append([int(fields[i]), int(fields[i+1])])
                        i += 2
                elif key == 'EXEC_RUNTIME':
                    # Execution runtime per device
                    while i < len(fields) and fields[i].replace('.', '', 1).isdigit():
                        self.exec_runtime.append(float(fields[i]))
                        i += 1
                elif key == 'CURKU':
                    self.curku = int(fields[i])
                    i += 1
                elif key == 'PROGRESS':
                    # Progress has two values: current and total
                    self.progress = [int(fields[i]), int(fields[i+1])]
                    i += 2
                elif key == 'RECHASH':
                    # Recovered hashes has two values: done and total
                    self.rec_hash = [int(fields[i]), int(fields[i+1])]
                    i += 2
                elif key == 'RECSALT':
                     # Recovered salts has two values: done and total
                    self.rec_salt = [int(fields[i]), int(fields[i+1])]
                    i += 2
                elif key == 'TEMP':
                    # Temperature per device
                    while i < len(fields) and fields[i].lstrip('-').isdigit():
                        self.temp.append(int(fields[i]))
                        i += 1
                elif key == 'REJECTED':
                    self.rejected = int(fields[i])
                    i += 1
                elif key == 'UTIL':
                    # Utilization per device
                    while i < len(fields) and fields[i].lstrip('-').isdigit():
                        self.util.append(int(fields[i]))
                        i += 1
                elif key == 'POWER':
                    # Power usage per device (newer versions)
                    while i < len(fields) and fields[i].lstrip('-').isdigit():
                        self.power.append(int(fields[i]))
                        i += 1
                else:
                    print(f"Unknown field in Hashcat status line: {key}")
                    self.unknown_fields = True
                    pass
        except (ValueError, IndexError) as e:
            print(f"Error parsing Hashcat status line: {e}")
            self.__init__("") # Fallback to default initialization

    def is_valid(self):
        return self.status >= 0

    def get_progress(self):
        return self.progress[0]

    def get_state(self):
        return self.status - 1

    def get_curku(self):
        return self.curku

    def get_temps(self):
        return self.temp

    def get_progress_total(self):
        return self.progress[1]

    def get_all_util(self):
        return self.util

    def get_util(self):
        if not self.util:
            return -1
        util_sum = 0
        for u in self.util:
            util_sum += u
        return int(util_sum/len(self.util))

    def get_speed(self):
        total_speed = 0
        for s in self.speed:
            total_speed += int(float(s[0]) * 1000 / s[1])
        return total_speed

    def get_rejected(self):
        return self.rejected

    def get_all_power(self):
        return self.power

    def get_power(self):
        if not self.power:
            return -1
        power_sum = 0
        for p in self.power:
            power_sum += p
        return int(power_sum / len(self.power))
