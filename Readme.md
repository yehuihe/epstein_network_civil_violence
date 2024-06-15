# Epstein Network Civil Violence Model

## Installation

### Dependencies

(venv) $ pip install -r requirements.txt

## Summary

This model is based on Joshua Epstein's simulation of how civil unrest grows and is suppressed. Citizen agents wander the grid randomly, and are endowed with individual risk aversion and hardship levels; there is also a universal regime legitimacy value. There are also Cop agents, who work on behalf of the regime. Cops arrest Citizens who are actively rebelling; Citizens decide whether to rebel based on their hardship and the regime legitimacy, and their perceived probability of arrest.

The model generates mass uprising as self-reinforcing processes: if enough agents are rebelling, the probability of any individual agent being arrested is reduced, making more agents more likely to join the uprising. However, the more rebelling Citizens the Cops arrest, the less likely additional agents become to join.

