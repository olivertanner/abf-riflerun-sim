from datetime import *
from random import *
import pandas as pd


class Participant:
    speed = 0
    shotgun_time = 0
    rifle_time = 0
    distance = 0
    state = 'Leg 1'
    shots = []
    penalty_distance = 0
    is_shooting = False

    def __init__(self):
        self.speed = avg_speed + (random() * speed_diff * 2) - speed_diff
        shoot_random = random()
        self.shotgun_time = (6 + (shoot_random * 3 * 2) - 3) * 60
        self.rifle_time = (4 + (shoot_random * 2 * 2) - 2) * 60

    def run(self, seconds):
        self.distance += self.speed / (60*60/seconds)

    def shoot(self, stand):
        if stand == 3:
            targets = 10
        else:
            targets = 5
        for shot in range(0, targets):
            self.shots.append(True)
            if random()*10 > stands_acc[stand-1]:
                self.shots[shot] = False
                self.penalty_distance += 0.25

    def change_state(self):
        self.state = sections[sections.index(str(self.state))+1]
        self.distance = 0
        self.shots.clear()

    def act(self):
        if not self.state == 'Finish':
            parts = str(self.state).split(' ')
            section_type = parts[0]
            section_number = int(parts[1])
            if section_type == 'Leg':
                leg_length = legs[section_number-1]
                if self.distance < leg_length:
                    self.run(loop_interval)
                else:
                    if section_number <= 3:
                        wait_queue[section_number - 1].append(self)
                    self.change_state()
                    self.act()
            elif section_type == 'Wait':
                if section_number == 3:
                    if stands[section_number-1] < shotguns and \
                            wait_queue[section_number-1].index(self) < shotguns - stands[section_number-1]:
                        self.change_state()
                        wait_queue[section_number - 1].remove(self)
                        self.act()
                else:
                    if stands[section_number-1] < 5 and \
                            wait_queue[section_number-1].index(self) < 5 - stands[section_number-1]:
                        self.change_state()
                        wait_queue[section_number - 1].remove(self)
                        self.act()
            elif section_type == 'Shoot':
                if section_number == 3:
                    if self.distance >= self.shotgun_time:
                        self.shoot(section_number)
                        self.is_shooting = False
                        stands[section_number - 1] -= 1
                        extra = self.distance - self.shotgun_time
                        self.change_state()
                        self.run(extra)
                        self.act()
                    else:
                        if not self.is_shooting:
                            self.is_shooting = True
                            stands[section_number - 1] += 1
                        self.distance += loop_interval
                else:
                    if self.distance >= self.rifle_time:
                        self.shoot(section_number)
                        self.is_shooting = False
                        stands[section_number - 1] -= 1
                        extra = self.distance - self.rifle_time
                        self.change_state()
                        self.run(extra)
                        self.act()
                    else:
                        if not self.is_shooting:
                            self.is_shooting = True
                            stands[section_number - 1] += 1
                        self.distance += loop_interval
            elif section_type == 'Penalty':
                if self.distance < self.penalty_distance:
                    self.run(loop_interval)
                if self.distance >= self.penalty_distance:
                    extra = self.distance - self.penalty_distance
                    self.change_state()
                    self.distance += extra
                    self.act()


script_run_id = 2
loop_interval = 5  # seconds
rows = []
intervals = [5, 6, 7]
shotguns_count = [5, 6, 7, 8]
for interval in intervals:
    for shotguns in shotguns_count:
        for sim_count in range(0, 100):

            # variables
            participant_count = 200
            speed_diff = 7
            avg_speed = 10

            # fixed
            time = datetime(2019, 4, 14, 9, 30, 0)
            wave_size = 5
            legs = [3.2, 3.1, 1.6, 2.1]
            stands = [0, 0, 0]
            stands_acc = [7.6, 6.6, 6.75]
            sections = ['Leg 1', 'Wait 1', 'Shoot 1', 'Penalty 1',
                        'Leg 2', 'Wait 2', 'Shoot 2', 'Penalty 2',
                        'Leg 3', 'Wait 3', 'Shoot 3', 'Penalty 3',
                        'Leg 4', 'Finish']
            start, finish = participant_count, 0
            participants, states = [], []
            wait_queue = [[] for _ in range(3)]
            count = 0

            while states.count('Finish') != participant_count:
                states.clear()
                if count % (interval * (60/loop_interval)) == 0 and len(participants) < participant_count:
                    for p in range(0, 5):
                        participants.append(Participant())
                        start -= 1
                for participant in participants:
                    participant.act()
                    states.append(participant.state)
                time += timedelta(seconds=loop_interval)
                # if count % 5 == 0:
                #     print(time.time())
                #     print('Start: ', start,
                #           '\n Leg 1: ', states.count('Leg 1'),
                #           ' | Wait 1: ', states.count('Wait 1'),
                #           ' | Shoot 1: ', states.count('Shoot 1'),
                #           ' | Penalty 1: ', states.count('Penalty 1'),
                #           '\n Leg 2: ', states.count('Leg 2'),
                #           ' | Wait 2: ', states.count('Wait 2'),
                #           ' | Shoot 2: ', states.count('Shoot 2'),
                #           ' | Penalty 2: ', states.count('Penalty 2'),
                #           '\n Leg 3: ', states.count('Leg 3'),
                #           ' | Wait 3: ', states.count('Wait 3'),
                #           ' | Shoot 3: ', states.count('Shoot 3'),
                #           ' | Penalty 3: ', states.count('Penalty 3'),
                #           '\n Leg 4: ', states.count('Leg 4'),
                #           ' | Finish: ', states.count('Finish'),
                #           '\n'
                #           )

                if time.second == 0:
                    rows.append({
                        'Sim_Id': sim_count,
                        'Time': time,
                        'Release_Interval': interval,
                        'Participants': participant_count,
                        'Shotguns': shotguns,
                        'Start': start,
                        'Leg_1': states.count('Leg 1'),
                        'Wait_1': states.count('Wait 1'),
                        'Shoot_1': states.count('Shoot 1'),
                        'Penalty_1': states.count('Penalty 1'),
                        'Leg_2': states.count('Leg 2'),
                        'Wait_2': states.count('Wait 2'),
                        'Shoot_2': states.count('Shoot 2'),
                        'Penalty_2': states.count('Penalty 2'),
                        'Leg_3': states.count('Leg 3'),
                        'Wait_3': states.count('Wait 3'),
                        'Shoot_3': states.count('Shoot 3'),
                        'Penalty_3': states.count('Penalty 3'),
                        'Leg_4': states.count('Leg 4'),
                        'Finish': states.count('Finish'),
                        'Script_Run_Id': script_run_id
                    })
                count += 1
            print(sim_count, ' ', interval, ' ', shotguns)

df = pd.DataFrame(rows, columns=[
            'Sim_Id',
            'Time',
            'Release_Interval',
            'Participants',
            'Shotguns',
            'Start',
            'Leg_1',
            'Wait_1',
            'Shoot_1',
            'Penalty_1',
            'Leg_2',
            'Wait_2',
            'Shoot_2',
            'Penalty_2',
            'Leg_3',
            'Wait_3',
            'Shoot_3',
            'Penalty_3',
            'Leg_4',
            'Finish'
        ])
path = 'C:/Users/otanner/Documents/External/ABF/simulations/sim_' + \
       datetime.now().__str__().split('.')[0].replace(':', '') + '.csv'
df.to_csv(path, index=True, encoding='utf-8')
print('File saved to: ', path)
