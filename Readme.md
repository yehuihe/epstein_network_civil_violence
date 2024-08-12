# Mean Field Civil Violence Model

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
### Plotting
To start the simulation and generate plots, open and run all cells in the Jupyter notebook:
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

This model is an extension of Joshua Epstein's simulation of how civil unrest grows and is suppressed. We design 2 different legitimacy hetrogeneous model, global heterogeneous and regional heterogeneous model to simulate different scenarios in real life. Additionally, we modify the legitimacy update mechanism by employing a mean-field approach, where the legitimacy of a citizen is influenced by the average legitimacy of their neighbors. We also varying deterrent effects of different jail terms on citizens (α), and the possible changing of citizen’s perception of regime legitimacy when they are jailed (jail factor). At last, we implement global sensitive analysis to important parameters with PAWN.

