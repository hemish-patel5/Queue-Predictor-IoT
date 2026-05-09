"""Test harness for pir_fsm.EventSequencer

Run this script to simulate rising-edge events and observe classification.
"""
import time
from pir_fsm import EventSequencer


def run_simulation():
    seq = EventSequencer(sequence_window=1.0, refractory=0.5)
    base = time.time()

    scenarios = [
        # Single person entering: A then B within 0.3s
        [('A', 0.0), ('B', 0.3)],
        # Single person exiting: B then A within 0.4s
        [('B', 2.0), ('A', 2.3)],
        # Two people quick back-to-back: A,B then A,B
        [('A', 4.0), ('B', 4.3), ('A', 5.0), ('B', 5.3)],
        # Noise: single A with no partner
        [('A', 7.0)],
        # Overlap: simultaneous-ish triggers
        [('A', 9.0), ('B', 9.05)],
    ]

    for scenario in scenarios:
        print('\nScenario:')
        for sensor, offset in scenario:
            ts = base + offset
            result = seq.add_event(sensor, ts)
            print(f'  Event {sensor}@{offset:.2f}s => {result}')
            # Allow time for refractory to pass in simulation by advancing base
        # reset sequence between scenarios for clarity
        seq = EventSequencer(sequence_window=1.0, refractory=0.5)


if __name__ == '__main__':
    run_simulation()
