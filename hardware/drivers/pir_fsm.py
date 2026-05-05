"""Simple PIR sequencing FSM helper

This module provides a pure-Python class EventSequencer that accepts rising-edge
events from two sensors ('A' and 'B') with timestamps and determines whether
they form an entry (A->B) or exit (B->A) sequence within a configurable window.

The implementation is deterministic and unit-testable.
"""
from collections import deque
import time


class EventSequencer:
    def __init__(self, sequence_window=1.0, refractory=0.6):
        """Create a new sequencer.

        sequence_window: max seconds between A->B or B->A to count as directional.
        refractory: seconds to ignore new events after a classified event.
        """
        self.sequence_window = float(sequence_window)
        self.refractory = float(refractory)
        self.events = deque()  # each item: (sensor: 'A'|'B', ts)
        self.last_classified_ts = 0

    def add_event(self, sensor: str, ts: float = None):
        """Add a rising-edge event for sensor 'A' or 'B' with timestamp ts (seconds).

        Returns:
            'entry' | 'exit' | 'motion' | None
            - 'entry' when A->B within window
            - 'exit' when B->A within window
            - 'motion' when single event couldn't be paired but still motion
            - None if ignored due to refractory
        """
        sensor = sensor.upper()
        if sensor not in ('A', 'B'):
            raise ValueError("sensor must be 'A' or 'B'")

        if ts is None:
            ts = time.time()

        # Respect refractory period
        if ts - self.last_classified_ts < self.refractory:
            return None

        # Add event
        self.events.append((sensor, ts))

        # Try to classify using the last two events
        while len(self.events) >= 2:
            s1, t1 = self.events[0]
            s2, t2 = self.events[1]

            # If sensors differ and are within sequence_window, classify
            if s1 != s2 and (t2 - t1) <= self.sequence_window:
                # A then B => entry; B then A => exit
                if s1 == 'A' and s2 == 'B':
                    self.events.popleft(); self.events.popleft()
                    self.last_classified_ts = t2
                    return 'entry'
                elif s1 == 'B' and s2 == 'A':
                    self.events.popleft(); self.events.popleft()
                    self.last_classified_ts = t2
                    return 'exit'
                else:
                    # Shouldn't happen, but consume one to avoid infinite loop
                    self.events.popleft()
                    return 'motion'
            else:
                # If second event is too old relative to first, drop the first
                if (t2 - t1) > self.sequence_window:
                    # classify first as motion (unpaired)
                    self.events.popleft()
                    self.last_classified_ts = t1
                    return 'motion'
                # Otherwise wait for a partner event
                break

        # Not enough info yet; leave in queue
        return None


if __name__ == '__main__':
    # Quick smoke test when run directly
    seq = EventSequencer(sequence_window=1.0, refractory=0.5)
    now = time.time()
    print(seq.add_event('A', now))          # None
    print(seq.add_event('B', now + 0.3))    # 'entry'
    print(seq.add_event('B', now + 2.0))    # None or 'motion' depending on refractory
