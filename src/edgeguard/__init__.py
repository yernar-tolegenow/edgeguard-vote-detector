"""EdgeGuard vote detector.

A small research tool for the master's thesis "Anomaly Detection and Autonomous
Threat Mitigation for Smart City IoT Infrastructure using Edge Computing".

It flags a reading only when at least two of three simple detectors agree, and
then picks a response with a small state machine.
"""

__version__ = "0.1.0"
