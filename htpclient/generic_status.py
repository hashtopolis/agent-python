class GenericStatus:
    """Class to parse hashcat status output"""

    def __init__(self, raw_line: str):
        # parse
        raw_line = raw_line.strip()
        self.line_parts = raw_line.split()
        self.valid = False
        self.progress = 0
        self.speed = 0

        if self.line_parts[0] != "STATUS" or len(self.line_parts) != 3:
            # invalid line
            return

        self.progress = int(self.line_parts[1])
        self.speed = int(self.line_parts[2])
        self.valid = True

    def is_valid(self):
        """Check if the status is valid"""
        return self.valid

    def get_progress(self):
        """Get the total progress"""
        return self.progress

    def get_speed(self):
        """Get the speed"""
        return self.speed
