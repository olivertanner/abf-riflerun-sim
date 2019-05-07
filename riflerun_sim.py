from datetime import datetime, timedelta
from random import random
import sys
import pandas as pd
import os

# initialise global variables
loop_interval = 5 # seconds, number of seconds simulated between each loop
rows = []
speed_diff = 7
avg_speed = 10

# Fixed
wave_size = 5 # number of Participants released per wave
legs = [3.2, 3.1, 1.6, 2.1] # distance in km of each leg
stands_acc = [7.6, 6.6, 6.75] # average shots / 10 hit at each stand
sections = ['Leg 1', 'Wait 1', 'Shoot 1', 'Penalty 1',
            'Leg 2', 'Wait 2', 'Shoot 2', 'Penalty 2',
            'Leg 3', 'Wait 3', 'Shoot 3', 'Penalty 3',
            'Leg 4', 'Finish']

class Participant:
    """
    An individual race Participant
    """
    # initialise variables
    speed = 0
    shotgun_time = 0
    rifle_time = 0
    distance = 0
    state = 'Leg 1'
    shots = []
    penalty_distance = 0
    is_shooting = False

    def __init__(self):
        """
        Initialises Participant with random running speed and shooting times based on average times
        """
        # average speed +/- random value between difference
        # e.g. avg_speed = 10, speed_diff = 7
        # 10 + random number between 0 and 14 - 7 = 10 +/- (0-7) = 3 - 17
        self.speed = avg_speed + (random() * speed_diff * 2) - speed_diff
        # keep same shooting random per person across all shots
        # assumes participant good at rifle shooting will be good at shotgun shooting
        shoot_random = random()
        # random shooting times in seconds between average range
        # average shotgun time 6 minutes +/- 3 minutes
        self.shotgun_time = (6 + (shoot_random * 3 * 2) - 3) * 60
        #average rifle time 4 minutes +/- 2 minutes
        self.rifle_time = (4 + (shoot_random * 2 * 2) - 2) * 60

    def run(self, seconds):
        """
        Increases run distance according to self's speed
        """
        self.distance += self.speed / (60*60/seconds)

    def shoot(self, stand):
        """
        Calculates how many shots the self hits at their current shooting stand
        """
        # if at shotgun stand
        if stand == 3:
            targets = 10
        else: # at a rifle stand
            targets = 5
        for shot in range(0, targets):
            # assume shot hit
            self.shots.append(True)
            # if the random value is higher than the stand's average
            if random()*10 > stands_acc[stand-1]:
                # set shot as miss and add 1 penalty lap
                self.shots[shot] = False
                self.penalty_distance += 0.25

    def change_state(self):
        """
        Change self state to the next section of the race
        and reset distance and shots for the new section
        """
        self.state = sections[sections.index(str(self.state))+1]
        self.distance = 0
        self.shots.clear()



def run_simulation(id, interval, shotguns, participant_count, start_time_str):
    """ Main function for running a simulation of the RifleRun

    Args:
        id (int): ID number for simulation.
        interval (int): Release interval in minutes between waves of participants.
        shotguns (int): Number of shotgun stands at the third shooting station.
        participant_count (int): Total number of participants taking part.
        start_time_str (str): Start time of the event in string format HH:mm:ss
    """
    # initialise simulation variables
    script_run_id = id # script run id to differentiate between simulations when merging resulting data
    time = datetime.strptime(start_time_str, "%H:%M:%S") # convert start time string to datetime object
    stands = [0, 0, 0] # number of people shooting at each stand
    start = participant_count # initialise start with number of Participants
    participants, states = [], []
    wait_queue = [[] for _ in range(3)] # create 3 empty lists for the 3 shooting stand queues
    sec_count = 0 # second counter

    def act(participant):
        """
        General act function which runs through different actions
        depending on the state of the Participant
        """
        if not participant.state == 'Finish':
            # split section into section type and number
            parts = str(participant.state).split(' ')
            section_type = parts[0]
            section_number = int(parts[1])
            if section_type == 'Leg':
                # get distance of leg
                leg_length = legs[section_number-1]
                # if not at end of the leg
                if participant.distance < leg_length:
                    participant.run(loop_interval)
                else: # finished leg
                    if section_number <= 3: #if not at finish
                        # join wait queue for next shoot station
                        wait_queue[section_number - 1].append(participant)
                    participant.change_state()
                    act(participant)
            elif section_type == 'Wait':
                # if in shotgun wait queue
                if section_number == 3:
                    # if shooting stands are not full and position in wait queue is less than available guns
                    if stands[section_number-1] < shotguns and \
                            wait_queue[section_number-1].index(participant) < shotguns - stands[section_number-1]:
                        # change state and remove Particpant from queue
                        participant.change_state()
                        wait_queue[section_number - 1].remove(participant)
                        act(participant)
                else: # rifle wait queue
                    # if shooting stands are not full and position in wait queue is less than available guns
                    if stands[section_number-1] < 5 and \
                            wait_queue[section_number-1].index(participant) < 5 - stands[section_number-1]:
                        # change state and remove Particpant from queue
                        participant.change_state()
                        wait_queue[section_number - 1].remove(participant)
                        act(participant)
            elif section_type == 'Shoot':
                # if at shotgun stand
                if section_number == 3:
                    # distance being used as time here
                    # if shotgun shooting time has been reached
                    if participant.distance >= participant.shotgun_time:
                        # calculate how many shots hit/missed and penalty distance
                        participant.shoot(section_number)
                        participant.is_shooting = False
                        # decrement number of Participants shooting at stand by 1
                        stands[section_number - 1] -= 1
                        # calculate leftover seconds after finishing shooting
                        extra = participant.distance - participant.shotgun_time
                        # change states and run for lefover seconds
                        participant.change_state()
                        participant.run(extra)
                        act(participant)
                    else: # not yet finished shooting
                        if not participant.is_shooting: # just got onto stand, not yet shooting
                            participant.is_shooting = True
                            # increment number of Participants shooting at stand by 1
                            stands[section_number - 1] += 1
                        # increase time spent at stand
                        participant.distance += loop_interval
                else: # at rifle stand
                    # distance being used as time here
                    # if shotgun shooting time has been reached
                    if participant.distance >= participant.rifle_time:
                        # calculate how many shots hit/missed and penalty distance
                        participant.shoot(section_number)
                        participant.is_shooting = False
                        # decrement number of Participants at shooting stand by 1
                        stands[section_number - 1] -= 1
                        # calculate the leftover seconds after finishing shooting
                        extra = participant.distance - participant.rifle_time
                        # change states and run for leftover seconds
                        participant.change_state()
                        participant.run(extra)
                        act(participant)
                    else: # not yet finished shooting
                        if not participant.is_shooting: # just got onto the stand, not yet shooting
                            participant.is_shooting = True
                            # increment the number of Participants at shooting stand by 1
                            stands[section_number - 1] += 1
                        # increase time spent at stand
                        participant.distance += loop_interval
            elif section_type == 'Penalty':
                # if distance is less than penalty distance, keep running
                if participant.distance < participant.penalty_distance:
                    participant.run(loop_interval)
                # if penalty distance has been reached
                if participant.distance >= participant.penalty_distance:
                    # calculate extra distance ran due to loop interval and change state
                    extra = participant.distance - participant.penalty_distance
                    participant.change_state()
                    participant.distance += extra
                    act(participant)

    # while not all Participants are finished
    while states.count('Finish') != participant_count:
        # clear participants previous states
        states.clear()
        # if elapsed time reaches next release interval 
        # and there are more participants to be released
        if sec_count % (interval * 60) == 0 and len(participants) < participant_count:
            for _ in range(0, wave_size):
                # create 5 new participants and reduce number at start
                participants.append(Participant())
                start -= 1
        for participant in participants:
            # perform actions for each participant, and add their final state to states
            act(participant)
            states.append(participant.state)
        # add the loop interval seconds to the current time
        time += timedelta(seconds=loop_interval)
        # output row for each minute
        if time.second == 0:
            rows.append({
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
        # add loop interval to elapsed time
        sec_count += loop_interval

    # convert row list to pandas dataframe
    df = pd.DataFrame(rows, columns=[
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
                'Finish',
                'Script_Run_Id'
            ])
    return df

def run_sim_to_csv(id, interval, shotguns, participant_count, start_time_str):
    df = run_simulation(id, interval, shotguns, participant_count, start_time_str)
    if not os.path.exists('simulations'):
        os.mkdir('simulations')
    # create output path in simulations folder using current time
    path = 'simulations/sim_' + \
        datetime.now().__str__().split('.')[0].replace(':', '') + '.csv'
    # output df to csv
    df.to_csv(path, index=False, encoding='utf-8')
    print('File saved to: ', path)

if __name__ == "__main__":
    id = int(input('Enter an id number: '))
    interval = int(input('Enter a release interval in minutes: '))
    shotguns = int(input('Enter an amount of shotguns: '))
    participant_count = int(input('Enter the number of participants: '))
    start_time_str = input('Enter the start time <HH:mm:ss>: ')
    if len(sys.argv):
        if sys.argv[1] == 'to_csv':
            run_sim_to_csv(id, interval, shotguns, participant_count, start_time_str)
        else:
            raise SystemExit("Usage: py riflerun_sim.py [to_csv]")
    else:
        run_simulation(id, interval, shotguns, participant_count, start_time_str)
