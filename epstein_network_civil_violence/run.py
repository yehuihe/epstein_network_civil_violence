from model import EpsteinCivilViolence
from server import server
from agent import Citizen

# Define the main function to set up and run the model
def run_simulation():
    height = 40
    width = 40
    citizen_density = 0.7
    cop_density = 0.04
    citizen_vision = 7
    cop_vision = 2
    legitimacy = 0.6
    max_jail_term = 15
    active_threshold = 0.1
    arrest_prob_constant = 2.3
    movement = True
    max_iters = 1000

    # Create an instance of the model
    model = EpsteinCivilViolence(
        width=width,
        height=height,
        citizen_density=citizen_density,
        cop_density=cop_density,
        citizen_vision=citizen_vision,
        cop_vision=cop_vision,
        legitimacy=legitimacy,
        max_jail_term=max_jail_term,
        active_threshold=active_threshold,
        arrest_prob_constant=arrest_prob_constant,
        movement=movement,
        max_iters=max_iters
    )

    for i in range(max_iters):
        model.step()


    # Print or analyze results
    # For instance, printing the final count of quiescent, active, and jailed citizens
    quiescent = len([agent for agent in model.schedule.agents if isinstance(agent, Citizen) and agent.condition == "Quiescent"])
    active = len([agent for agent in model.schedule.agents if isinstance(agent, Citizen) and agent.condition == "Active"])
    jailed = len([agent for agent in model.schedule.agents if isinstance(agent, Citizen) and agent.jail_sentence > 0])
    print(f"Final counts - Quiescent: {quiescent}, Active: {active}, Jailed: {jailed}")

if __name__ == "__main__":
    run_simulation()
    server.launch()
