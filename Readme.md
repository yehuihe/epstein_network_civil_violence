# Epstein Network Civil Violence Model

## Installation
### Clone the Repository
```bash
git clone https://github.com/yehuihe/epstein_network_civil_violence.git
cd epstein_network_civil_violence
```
### Dependencies
```bash
pip install -r requirements.txt
```

## Execution
### Run the Simulation
To start the simulation, execute:
```bash
python run_network.py
```

### Plotting
To generate plots, open and run all cells in the Jupyter notebook:
```bash
jupyter notebook "simulation (final version).ipynb"
```

### Global Sensitivity Analysis
To perform global sensitivity analysis, open and run all cells in the Jupyter notebook:
```bash
jupyter notebook PAWN_analysis.ipynb
```

## Acknowledgments

This project uses code from the [Mesa Examples](https://github.com/projectmesa/mesa-examples/tree/main/examples/epstein_civil_violence) repository, specifically the Epstein Civil Violence model example, which are put into epstein_civil_violence/agent.py and epstein_civil_violence/model.py in our project. The original code was created and maintained by the Mesa project contributors.

## Summary

This model is based on Joshua Epstein's simulation of how civil unrest grows and is suppressed. Citizen agents wander the grid randomly, and are endowed with individual risk aversion and hardship levels; there is also a universal regime legitimacy value. There are also Cop agents, who work on behalf of the regime. Cops arrest Citizens who are actively rebelling; Citizens decide whether to rebel based on their hardship and the regime legitimacy, and their perceived probability of arrest.

The model generates mass uprising as self-reinforcing processes: if enough agents are rebelling, the probability of any individual agent being arrested is reduced, making more agents more likely to join the uprising. However, the more rebelling Citizens the Cops arrest, the less likely additional agents become to join.

