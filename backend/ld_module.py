class LadderRung:
    def __init__(self, title, ascii_rung, notes=None):
        self.title = title
        self.ascii_rung = ascii_rung
        self.notes = notes or ""


class LDGenerator:

    @staticmethod
    def generate_bottle_filling():

        rungs = []

        # Rung 1: Timer activation
        rungs.append(LadderRung(
            title="Rung 1 – Timer Activation",
            ascii_rung="""
| BottleSensor |----[ TON FillTimer ]----|
                 PT = 5s
"""
        ))

        # Rung 2: Valve control
        rungs.append(LadderRung(
            title="Rung 2 – Filling Valve Control",
            ascii_rung="""
| FillTimer.Q |----------------( FillValve )
"""
        ))

        # Rung 3: Conveyor stop
        rungs.append(LadderRung(
            title="Rung 3 – Stop Conveyor",
            ascii_rung="""
| BottleSensor |----------------( /ConveyorMotor )
"""
        ))

        # Rung 4: Conveyor restart
        rungs.append(LadderRung(
            title="Rung 4 – Restart Conveyor",
            ascii_rung="""
| NOT FillTimer.Q |------------( ConveyorMotor )
"""
        ))

        return rungs


    @staticmethod
    def generate_alarm_system():
        rungs = []
        # Rung 1: High Temp Alarm
        rungs.append(LadderRung(
            title="Rung 1 – High Temperature Alarm",
            ascii_rung="""
| TempSensor > 100 |----( AlarmSiren )
"""
        ))
        # Rung 2: E-Stop Logic
        rungs.append(LadderRung(
            title="Rung 2 – Emergency Stop",
            ascii_rung="""
| E_Stop_Button |----( /MainContactor )
"""
        ))
        # Rung 3: Low Pressure Warning
        rungs.append(LadderRung(
            title="Rung 3 – Low Pressure Warning",
            ascii_rung="""
| Pressure < 10 |----( WarningLight )
"""
        ))
        return rungs


def generate_ld(domain: str):
    d = domain.lower()
    if "bottle" in d or "fill" in d:
        return LDGenerator.generate_bottle_filling()
    if "alarm" in d or "event" in d or "monitor" in d:
        return LDGenerator.generate_alarm_system()

    # Default fallback
    return [
        LadderRung(
            title="Default Rung",
            ascii_rung="""
| Start |----------------( Motor )
"""
        )
    ]
