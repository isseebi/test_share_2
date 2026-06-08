class UserSystemParameters:
    def __init__(self, system_name: str, kp: float, kvp: float, kvi: float, notes: str):
        self.system_name = system_name
        self.kp = kp
        self.kvp = kvp
        self.kvi = kvi
        self.notes = notes

    def to_dict(self) -> dict:
        return {
            "system_name": self.system_name,
            "kp": self.kp,
            "kvp": self.kvp,
            "kvi": self.kvi,
            "notes": self.notes
        }
